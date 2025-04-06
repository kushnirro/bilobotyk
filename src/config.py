from typing import Dict, Union, List

# Словник населених пунктів Білобожницької громади та їх координати
SETTLEMENTS: Dict[str, Dict[str, float]] = {
    "Білобожниця": {"lat": 49.0261, "lon": 25.7357},
    "Білий Потік": {"lat": 49.0767, "lon": 25.6775},
    "Звиняч": {"lat": 49.0419, "lon": 25.7619},
    "Семаківці": {"lat": 49.0461, "lon": 25.6951},
    "Ромашівка": {"lat": 48.9974, "lon": 25.7439},
    "Мазурівка": {"lat": 49.0114, "lon": 25.6873},
    "Калинівщина": {"lat": 49.0008, "lon": 25.7113},
    "Джурин": {"lat": 48.9711, "lon": 25.7611},
    "Палашівка": {"lat": 48.9533, "lon": 25.8004},
    "Косів": {"lat": 48.9325, "lon": 25.7663},
}

# Налаштування кешування
WEATHER_CACHE_TIMEOUT: int = 1800  # 30 хвилин у секундах
FORECAST_CACHE_TIMEOUT: int = 3600  # 1 година у секундах
NEWS_CACHE_TIMEOUT = 1800  # 30 хвилин у секундах

# Налаштування API
WEATHER_API_TIMEOUT: int = 10  # секунд

# Налаштування сповіщень
DEFAULT_NOTIFICATION_TIMES: List[str] = ["08:00", "14:00", "20:00"]  # Стандартні часи сповіщень
MAX_NOTIFICATIONS_PER_USER: int = 5  # Максимальна кількість сповіщень для одного користувача

# Джерела новин
NEWS_SOURCES = {
    "suspilne": {
        "name": "Суспільне Тернопіль",
        "url": "https://suspilne.media/ternopil/",
        "icon": "📰"
    }
    # Тут можна додати інші джерела новин
}

# Емодзі для різних типів погоди
WEATHER_EMOJIS: Dict[str, str] = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
    "Smoke": "🌫️",
    "Dust": "🌫️",
    "Sand": "🌫️",
    "Ash": "🌫️",
    "Squall": "💨",
    "Tornado": "🌪️"
} 