import os
import json
import uuid
from src.calendar_utils import time_to_minutes

DATA_FILE = os.path.join("data", "schedule.json")

def load_schedule():
    """Загружает расписание из JSON-файла"""
    if not os.path.exists(DATA_FILE):
        # Если файла нет, инициализируем пустую структуру
        initial_data = {str(i): [] for i in range(7)}
        save_schedule(initial_data)
        return initial_data
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schedule(data):
    """Сохраняет расписание в JSON-файл"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_time_collision(day_index, time_start, time_end, exclude_slot_id=None):
    """
    Проверяет, пересекается ли новое время со старыми слотами в этот день.
    exclude_slot_id нужен, чтобы не проверять слот сам с собой при редактировании.
    Возвращает True, если есть наложение (ошибка), и False, если всё чисто.
    """
    schedule = load_schedule()
    day_slots = schedule.get(str(day_index), [])
    
    new_start = time_to_minutes(time_start)
    new_end = time_to_minutes(time_end)
    
    # Валидация: конец не может быть раньше начала
    if new_start >= new_end:
        return True
        
    for slot in day_slots:
        if exclude_slot_id and slot["id"] == exclude_slot_id:
            continue
            
        exist_start = time_to_minutes(slot["time_start"])
        exist_end = time_to_minutes(slot["time_end"])
        
        # Условие пересечения интервалов времени
        if new_start < exist_end and exist_start < new_end:
            return True # Наложение обнаружено!
            
    return False

def add_slot(day_index, time_start, time_end, student, subject):
    """
    Добавляет новый слот.
    Возвращает (True, "Успешно") или (False, "Сообщение об ошибке").
    """
    if check_time_collision(day_index, time_start, time_end):
        return False, "Ошибка: Это время уже занято другим учеником или указано неверно!"
        
    schedule = load_schedule()
    
    new_slot = {
        "id": str(uuid.uuid4()), # Генерируем уникальный ID для кнопок уд./ред.
        "time_start": time_start,
        "time_end": time_end,
        "student": student,
        "subject": subject
    }
    
    schedule[str(day_index)].append(new_slot)
    
    # Сортируем слоты дня по времени начала, чтобы они в таблице шли по порядку
    schedule[str(day_index)].sort(key=lambda x: time_to_minutes(x["time_start"]))
    
    save_schedule(schedule)
    return True, "Слот успешно добавлен"

def delete_slot(day_index, slot_id):
    """Удаляет слот по его уникальному ID"""
    schedule = load_schedule()
    day_slots = schedule.get(str(day_index), [])
    
    # Фильтруем список, оставляя всё, кроме нужного ID
    schedule[str(day_index)] = [s for s in day_slots if s["id"] != slot_id]
    
    save_schedule(schedule)

def update_slot(day_index, slot_id, time_start, time_end, student, subject):
    """
    Обновляет существующий слот с проверкой наложений.
    Возвращает (True, "Успешно") или (False, "Сообщение об ошибке").
    """
    if check_time_collision(day_index, time_start, time_end, exclude_slot_id=slot_id):
        return False, "Ошибка: Новое время пересекается с существующими занятиями!"
        
    schedule = load_schedule()
    day_slots = schedule.get(str(day_index), [])
    
    for slot in day_slots:
        if slot["id"] == slot_id:
            slot["time_start"] = time_start
            slot["time_end"] = time_end
            slot["student"] = student
            slot["subject"] = subject
            break
            
    schedule[str(day_index)].sort(key=lambda x: time_to_minutes(x["time_start"]))
    save_schedule(schedule)
    return True, "Слот успешно обновлен"
