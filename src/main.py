import telebot
from telebot import types
import requests
import datetime
import json
import os
import logging
import threading
import time
from dotenv import load_dotenv
from config import (
    SETTLEMENTS, WEATHER_CACHE_TIMEOUT, WEATHER_API_TIMEOUT, 
    WEATHER_EMOJIS, FORECAST_CACHE_TIMEOUT, DEFAULT_NOTIFICATION_TIMES,
    MAX_NOTIFICATIONS_PER_USER, NEWS_SOURCES
)
from holidays import get_all_holidays
from database import Database
from news import NewsLinks

# Налаштування логування
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Завантаження змінних оточення
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if not os.path.exists(env_path):
    raise FileNotFoundError(f"Файл .env не знайдено за шляхом: {env_path}")
load_dotenv(env_path)

# Отримання ключів API з змінних оточення
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Перевірка наявності необхідних токенів
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не знайдено в змінних оточення")
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY не знайдено в змінних оточення")

# Створення бота, бази даних та парсера новин
bot = telebot.TeleBot(BOT_TOKEN)
db = Database()
news_parser = NewsLinks()

# Кеші для даних
weather_cache = {}
forecast_cache = {}

# Список свят
holidays = get_all_holidays()

# Функція для отримання погоди
def get_weather(lat, lon):
    cache_key = f"{lat}_{lon}"
    current_time = time.time()
    
    # Перевірка кешу
    if cache_key in weather_cache:
        cached_data = weather_cache[cache_key]
        if current_time - cached_data['timestamp'] < WEATHER_CACHE_TIMEOUT:
            return cached_data['data']
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=uk"
        response = requests.get(url, timeout=WEATHER_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        weather_description = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        
        weather_emoji = get_weather_emoji(data["weather"][0]["main"])
        
        weather_info = (
            f"{weather_emoji} *Погода:* {weather_description}\n"
            f"🌡️ *Температура:* {temp:.1f}°C\n"
            f"🌡️ *Відчувається як:* {feels_like:.1f}°C\n"
            f"💧 *Вологість:* {humidity}%\n"
            f"💨 *Швидкість вітру:* {wind_speed} м/с"
        )
        
        # Зберігання в кеші
        weather_cache[cache_key] = {
            'data': weather_info,
            'timestamp': current_time
        }
        
        return weather_info
    except requests.RequestException as e:
        logger.error(f"Помилка запиту до API погоди: {e}")
        return "❌ Не вдалося отримати дані про погоду. Спробуйте пізніше."
    except KeyError as e:
        logger.error(f"Помилка обробки даних погоди: {e}")
        return "❌ Помилка обробки даних погоди. Спробуйте пізніше."
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}")
        return "❌ Сталася неочікувана помилка. Спробуйте пізніше."

# Функція для отримання відповідного емодзі до погоди
def get_weather_emoji(weather_main):
    return WEATHER_EMOJIS.get(weather_main, "🌈")

# Перевірка свят для поточного дня
def get_today_holidays():
    today = datetime.datetime.now()
    holidays = get_all_holidays(today.year)
    today_key = today.strftime("%m-%d")
    
    if today_key in holidays:
        return f"📅 *Сьогодні:* {holidays[today_key]}"
    return "📅 *Сьогодні немає державних або релігійних свят.*"

def get_weather_forecast(lat, lon):
    """Отримати прогноз погоди на 5 днів"""
    cache_key = f"{lat}_{lon}"
    current_time = time.time()
    
    if cache_key in forecast_cache:
        cached_data = forecast_cache[cache_key]
        if current_time - cached_data['timestamp'] < FORECAST_CACHE_TIMEOUT:
            return cached_data['data']
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=uk"
        response = requests.get(url, timeout=WEATHER_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        forecast_info = []
        current_date = None
        
        for item in data['list']:
            date = datetime.datetime.fromtimestamp(item['dt'])
            if current_date != date.date():
                current_date = date.date()
                
                weather = item['weather'][0]
                temp = item['main']['temp']
                weather_emoji = get_weather_emoji(weather['main'])
                
                forecast_info.append(
                    f"\n📅 *{date.strftime('%d.%m.%Y')}*:\n"
                    f"{weather_emoji} {weather['description'].capitalize()}\n"
                    f"🌡️ Температура: {temp:.1f}°C"
                )
        
        result = "🔮 *Прогноз погоди на 5 днів:*\n" + "\n".join(forecast_info)
        
        forecast_cache[cache_key] = {
            'data': result,
            'timestamp': current_time
        }
        
        return result
    except Exception as e:
        logger.error(f"Помилка отримання прогнозу погоди: {e}")
        return "❌ Не вдалося отримати прогноз погоди. Спробуйте пізніше."

def show_notification_settings(message):
    """Показати налаштування сповіщень"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Отримуємо поточні налаштування
    current_times = db.get_user_notifications(message.chat.id)
    
    # Додаємо кнопки для стандартних часів
    for time in DEFAULT_NOTIFICATION_TIMES:
        text = f"{'✅' if time in current_times else '❌'} {time}"
        markup.add(types.InlineKeyboardButton(
            text, callback_data=f"toggle_notification_{time}"
        ))
    
    markup.add(types.InlineKeyboardButton(
        "🔄 Зберегти налаштування", callback_data="save_notifications"
    ))
    
    bot.send_message(
        message.chat.id,
        "⚙️ *Налаштування сповіщень про погоду*\n\n"
        "Оберіть час, коли ви хочете отримувати сповіщення про погоду:\n"
        "✅ - сповіщення увімкнено\n"
        "❌ - сповіщення вимкнено",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def show_news_sources(message):
    """Показати доступні джерела новин"""
    news = news_parser.get_news_sources()
    bot.send_message(
        message.chat.id,
        news,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# Оновлюємо обробник команди /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    weather_button = types.KeyboardButton('🌤️ Погода')
    forecast_button = types.KeyboardButton('🔮 Прогноз')
    news_button = types.KeyboardButton('📰 Новини')
    holiday_button = types.KeyboardButton('📅 Свята сьогодні')
    settings_button = types.KeyboardButton('⚙️ Налаштування')
    markup.add(weather_button, forecast_button, news_button, holiday_button, settings_button)
    
    welcome_message = (
        "Вітаю! Я бот Білобожницької громади. 👋\n\n"
        "Я можу показати вам:\n"
        "- Поточну погоду 🌤️\n"
        "- Прогноз погоди на 5 днів 🔮\n"
        "- Останні новини 📰\n"
        "- Свята та визначні дати 📅\n"
        "- Налаштувати сповіщення про погоду ⚙️"
    )
    
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

# Обробник команди /weather
@bot.message_handler(commands=['weather'])
def weather_command(message):
    show_settlement_selection(message, "weather")

# Обробник команди /forecast
@bot.message_handler(commands=['forecast'])
def forecast_command(message):
    show_settlement_selection(message, "forecast")

# Обробник команди /news
@bot.message_handler(commands=['news'])
def news_command(message):
    show_news_sources(message)

# Обробник команди /holiday
@bot.message_handler(commands=['holiday'])
def holiday_command(message):
    holiday_info = get_today_holidays()
    bot.send_message(message.chat.id, holiday_info, parse_mode="Markdown")

# Обробник команди /settings
@bot.message_handler(commands=['settings'])
def settings_command(message):
    show_notification_settings(message)

# Показати меню вибору населених пунктів
def show_settlement_selection(message, action_type="weather"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for settlement in SETTLEMENTS:
        callback_data = f"{action_type}_{settlement}"
        buttons.append(types.InlineKeyboardButton(settlement, callback_data=callback_data))
    
    markup.add(*buttons)
    
    title = "Оберіть населений пункт для отримання"
    if action_type == "weather":
        title += " погоди"
    else:
        title += " прогнозу погоди"
    
    bot.send_message(message.chat.id, title, reply_markup=markup)

# Обробник натискання кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("weather_"):
        settlement = call.data.split("_")[1]
        if settlement in SETTLEMENTS:
            lat = SETTLEMENTS[settlement]["lat"]
            lon = SETTLEMENTS[settlement]["lon"]
            weather_info = get_weather(lat, lon)
            message_text = f"*Погода у {settlement}*\n\n{weather_info}"
            bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")
            
            # Зберігаємо вибраний населений пункт
            db.save_user_settlement(call.message.chat.id, settlement)
    
    elif call.data.startswith("forecast_"):
        settlement = call.data.split("_")[1]
        if settlement in SETTLEMENTS:
            lat = SETTLEMENTS[settlement]["lat"]
            lon = SETTLEMENTS[settlement]["lon"]
            forecast_info = get_weather_forecast(lat, lon)
            message_text = f"*Прогноз погоди для {settlement}*\n\n{forecast_info}"
            bot.send_message(call.message.chat.id, message_text, parse_mode="Markdown")
    
    elif call.data.startswith("news_"):
        source = call.data.split("_")[1]
        news = news_parser.get_source_link(source)
        bot.send_message(call.message.chat.id, news, parse_mode="Markdown", disable_web_page_preview=False)
    
    elif call.data.startswith("toggle_notification_"):
        time = call.data.split("_")[2]
        current_times = db.get_user_notifications(call.message.chat.id)
        
        if time in current_times:
            current_times.remove(time)
        elif len(current_times) < MAX_NOTIFICATIONS_PER_USER:
            current_times.append(time)
        
        db.save_user_notifications(call.message.chat.id, current_times)
        show_notification_settings(call.message)
    
    elif call.data == "save_notifications":
        bot.send_message(
            call.message.chat.id,
            "✅ Налаштування сповіщень збережено!"
        )
    
    bot.answer_callback_query(call.id)

# Обробник текстових повідомлень
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == '🌤️ Погода':
        show_settlement_selection(message, "weather")
    elif message.text == '🔮 Прогноз':
        show_settlement_selection(message, "forecast")
    elif message.text == '📰 Новини':
        show_news_sources(message)
    elif message.text == '📅 Свята сьогодні':
        holiday_info = get_today_holidays()
        bot.send_message(message.chat.id, holiday_info, parse_mode="Markdown")
    elif message.text == '⚙️ Налаштування':
        show_notification_settings(message)
    else:
        bot.send_message(
            message.chat.id,
            "Оберіть функцію за допомогою кнопок нижче або використайте команди:\n"
            "/weather - Погода\n"
            "/forecast - Прогноз\n"
            "/news - Новини\n"
            "/holiday - Свята\n"
            "/settings - Налаштування"
        )

# Функція для надсилання сповіщень
def send_weather_notifications():
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")
        users = db.get_users_for_notification(current_time)
        
        for user in users:
            if user["settlement"] in SETTLEMENTS:
                lat = SETTLEMENTS[user["settlement"]]["lat"]
                lon = SETTLEMENTS[user["settlement"]]["lon"]
                weather_info = get_weather(lat, lon)
                message_text = f"🔔 *Сповіщення про погоду у {user['settlement']}*\n\n{weather_info}"
                
                try:
                    bot.send_message(user["user_id"], message_text, parse_mode="Markdown")
                    db.update_last_notification(user["user_id"])
                except Exception as e:
                    logger.error(f"Помилка надсилання сповіщення користувачу {user['user_id']}: {e}")
        
        # Чекаємо 1 хвилину перед наступною перевіркою
        time.sleep(60)

# Запуск бота
if __name__ == "__main__":
    # Запускаємо потік для сповіщень
    notification_thread = threading.Thread(target=send_weather_notifications, daemon=True)
    notification_thread.start()
    
    print("Бот запущено!")
    bot.polling(none_stop=True)