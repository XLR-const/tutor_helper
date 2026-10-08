import os
import json
import uuid
from src.calendar_utils import time_to_minutes

DATA_FILE = os.path.join("data", "schedule.json")

def load_schedule():
    """Загружает расписание из JSON-файла с принудительной валидацией новой структуры"""
    # 1. Если файла вообще нет, создаем чистую структуру
    if not os.path.exists(DATA_FILE):
        initial_data = {str(i): {"green_line": None, "slots": []} for i in range(7)}
        save_schedule(initial_data)
        return initial_data
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # Если файл повредился, сбрасываем в дефолт
            data = {}

    # 2. Принудительная нормализация структуры (лечит любые конфликты версий)
    cleaned_data = {}
    for i in range(7):
        day_str = str(i)
        
        # Если дня нет или структура старая (была просто списком)
        if day_str not in data or isinstance(data[day_str], list):
            old_slots = data[day_str] if day_str in data and isinstance(data[day_str], list) else []
            cleaned_data[day_str] = {"green_line": None, "slots": old_slots}
        elif isinstance(data[day_str], dict):
            # Если это словарь, проверяем наличие нужных ключей
            green = data[day_str].get("green_line", None)
            slots = data[day_str].get("slots", [])
            # Гарантируем, что slots — это всегда список
            if not isinstance(slots, list):
                slots = []
            cleaned_data[day_str] = {"green_line": green, "slots": slots}
        else:
            cleaned_data[day_str] = {"green_line": None, "slots": []}

    # Если данные пришлось чистить, сразу сохраняем исправленный вариант
    if cleaned_data != data:
        save_schedule(cleaned_data)
        
    return cleaned_data


def save_schedule(data):
    """Сохраняет расписание"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def set_green_line(day_index, time_str):
    """Устанавливает или обновляет Green Line для конкретного дня"""
    schedule = load_schedule()
    if time_str:
        # Проверяем формат времени
        try:
            time_to_minutes(time_str)
            schedule[str(day_index)]["green_line"] = time_str
        except:
            return False, "Неверный формат времени"
    else:
        schedule[str(day_index)]["green_line"] = None
        
    save_schedule(schedule)
    return True, "Green Line успешно установлена"

def check_time_collision(day_index, time_start, time_end, exclude_slot_id=None):
    """Проверяет наложения с другими слотами и с Green Line"""
    schedule = load_schedule()
    day_data = schedule.get(str(day_index), {"green_line": None, "slots": []})
    
    new_start = time_to_minutes(time_start)
    new_end = time_to_minutes(time_end)
    
    if new_start >= new_end:
        return True, "Время окончания должно быть позже времени начала!"
        
    # ПРОВЕРКА GREEN LINE: Урок не может начаться раньше границы личных дел
    if day_data["green_line"]:
        green_limit = time_to_minutes(day_data["green_line"])
        if new_start < green_limit:
            return True, f"Нельзя поставить слот! Это время занято личными делами (Green Line до {day_data['green_line']})."
            
    # Проверка наложений с другими уроками
    for slot in day_data["slots"]:
        if exclude_slot_id and slot["id"] == exclude_slot_id:
            continue
            
        exist_start = time_to_minutes(slot["time_start"])
        exist_end = time_to_minutes(slot["time_end"])
        
        if new_start < exist_end and exist_start < new_end:
            return True, "Это время уже занято другим учеником!"
            
    return False, ""

def add_slot(day_index, time_start, time_end, student, subject):
    is_collision, error_message = check_time_collision(day_index, time_start, time_end)
    if is_collision:
        return False, error_message
        
    schedule = load_schedule()
    new_slot = {
        "id": str(uuid.uuid4()),
        "time_start": time_start,
        "time_end": time_end,
        "student": student,
        "subject": subject
    }
    schedule[str(day_index)]["slots"].append(new_slot)
    schedule[str(day_index)]["slots"].sort(key=lambda x: time_to_minutes(x["time_start"]))
    
    save_schedule(schedule)
    return True, "Слот успешно добавлен"

def delete_slot(day_index, slot_id):
    schedule = load_schedule()
    schedule[str(day_index)]["slots"] = [s for s in schedule[str(day_index)]["slots"] if s["id"] != slot_id]
    save_schedule(schedule)

def update_slot(day_index, slot_id, time_start, time_end, student, subject):
    is_collision, error_message = check_time_collision(day_index, time_start, time_end, exclude_slot_id=slot_id)
    if is_collision:
        return False, error_message
        
    schedule = load_schedule()
    for slot in schedule[str(day_index)]["slots"]:
        if slot["id"] == slot_id:
            slot["time_start"] = time_start
            slot["time_end"] = time_end
            slot["student"] = student
            slot["subject"] = subject
            break
            
    schedule[str(day_index)]["slots"].sort(key=lambda x: time_to_minutes(x["time_start"]))
    save_schedule(schedule)
    return True, "Слот успешно обновлен"

def clear_all_weeks():
    """Полностью очищает все слоты и границы во всех 7 днях недели"""
    empty_structure = {
        str(i): {"green_line": None, "slots": []} for i in range(7)
    }
    save_schedule(empty_structure)
    return True
