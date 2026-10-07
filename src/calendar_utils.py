import datetime

# Статичные названия дней для заголовков
DAYS_RU = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

def get_current_week_dates():
    """
    Вычисляет даты для каждого дня текущей недели (от ПН до ВС) с учетом ГОДА.
    Возвращает список строк формата "ДД.ММ.ГГГГ" (например, ['05.10.2026', '06.10.2026', ...]).
    """
    today = datetime.date.today()
    # Находим понедельник текущей недели
    monday = today - datetime.timedelta(days=today.weekday())
    
    week_dates = []
    for i in range(7):
        day_date = monday + datetime.timedelta(days=i)
        week_dates.append(day_date.strftime("%d.%m.%Y")) # %Y добавляет 4 цифры года
        
    return week_dates


def get_current_day_index():
    """Возвращает индекс текущего дня недели (0 = ПН, 6 = ВС)"""
    return datetime.date.today().weekday()

def time_to_minutes(time_str):
    """Вспомогательная функция: переводит 'ЧЧ:ММ' в количество минут от начала суток"""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def find_nearest_slot(slots_today):
    """
    Среди слотов на СЕГОДНЯ находит тот, который начнется скоро или идет прямо сейчас.
    Возвращает ID ближайшего слота или None, если занятий больше нет.
    """
    if not slots_today:
        return None
        
    now = datetime.datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    nearest_slot_id = None
    min_diff = float('inf')
    
    for slot in slots_today:
        start_min = time_to_minutes(slot["time_start"])
        end_min = time_to_minutes(slot["time_end"])
        
        # 1. Если занятие идет прямо сейчас — оно имеет высший приоритет
        if start_min <= current_minutes < end_min:
            return slot["id"]
            
        # 2. Если занятие еще впереди, ищем самое близкое по времени
        if start_min > current_minutes:
            diff = start_min - current_minutes
            if diff < min_diff:
                min_diff = diff
                nearest_slot_id = slot["id"]
                
    return nearest_slot_id
