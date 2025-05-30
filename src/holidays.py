from datetime import datetime, timedelta
import calendar

def calculate_easter(year):
    """Calculate the date of Orthodox Easter using Meeus's algorithm."""
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + 15) % 30
    e = (2 * b + 4 * c + 6 * d + 6) % 7
    f = d + e
    
    if f <= 9:
        day = f + 22
        month = 3
    else:
        day = f - 9
        month = 4
    
    # Convert from Julian to Gregorian calendar
    julian_date = datetime(year, month, day)
    gregorian_date = julian_date + timedelta(days=13)
    
    return gregorian_date.strftime("%m-%d")

def calculate_vyshyvanka_day(year):
    """Calculate Vyshyvanka Day (third Thursday in May)."""
    c = calendar.monthcalendar(year, 5)
    thursdays = [week[calendar.THURSDAY] for week in c if week[calendar.THURSDAY] != 0]
    third_thursday = thursdays[2]
    return f"05-{third_thursday:02d}"

def calculate_trinity_day(year):
    """Calculate Trinity Day (50 days after Easter)."""
    easter_date = datetime.strptime(f"{year}-{calculate_easter(year)}", "%Y-%m-%d")
    trinity_date = easter_date + timedelta(days=49)
    return trinity_date.strftime("%m-%d")

def get_dynamic_holidays(year):
    """Get holidays with dynamic dates for a specific year."""
    return {
        calculate_easter(year): "🐣 Великдень",
        calculate_vyshyvanka_day(year): "🌺 День вишиванки",
        calculate_trinity_day(year): "🌿 Трійця"
    }

# Static holidays and significant dates
STATIC_HOLIDAYS = {
    # Січень
    "01-01": "🎄 Новий рік",
    "01-06": "🌟 Святвечір",
    "01-07": "🎄 Різдво Христове (за юліанським календарем)",
    "01-14": "🎉 Старий Новий рік",
    "01-22": "🇺🇦 День Соборності України",
    "01-27": "🕯️ Міжнародний день пам'яті жертв Голокосту",
    
    # Лютий
    "02-15": "🕯️ День вшанування учасників бойових дій на території інших держав",
    "02-20": "🕯️ День Героїв Небесної Сотні",
    
    # Березень
    "03-08": "🌷 Міжнародний жіночий день",
    "03-09": "📚 День народження Тараса Шевченка",
    "03-14": "🇺🇦 День українського добровольця",
    
    # Квітень
    "04-26": "🕯️ День чорнобильської трагедії",
    
    # Травень
    "05-01": "🌱 День праці",
    "05-08": "🕯️ День пам'яті та примирення",
    "05-09": "🎖️ День перемоги над нацизмом у Другій світовій війні",
    "05-15": "👨‍👩‍👧‍👦 Міжнародний день сім'ї",
    
    # Червень
    "06-01": "👶 Міжнародний день захисту дітей",
    "06-28": "🇺🇦 День Конституції України",
    
    # Липень
    "07-28": "🇺🇦 День Української Державності",
    
    # Серпень
    "08-24": "🇺🇦 День Незалежності України",
    
    # Вересень
    "09-01": "🎓 День знань",
    "09-30": "📚 День бібліотек",
    
    # Жовтень
    "10-01": "🎵 Міжнародний день музики",
    "10-14": "🎖️ День захисників і захисниць України",
    
    # Листопад
    "11-09": "📚 День української писемності та мови",
    "11-21": "🇺🇦 День Гідності та Свободи",
    "11-26": "🕯️ День пам'яті жертв голодоморів",
    
    # Грудень
    "12-06": "🎖️ День Збройних Сил України",
    "12-19": "🎅 День Святого Миколая",
    "12-25": "🎄 Різдво Христове (за григоріанським календарем)"
}

def get_all_holidays(year=None):
    """Get all holidays including dynamic dates."""
    if year is None:
        year = datetime.now().year
        
    all_holidays = STATIC_HOLIDAYS.copy()
    all_holidays.update(get_dynamic_holidays(year))
    return all_holidays 