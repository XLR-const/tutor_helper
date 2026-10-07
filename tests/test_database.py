import os
import unittest
import json
from src import database

class TestTutorDatabase(unittest.TestCase):
    
    def setUp(self):
        """Выполняется ПЕРЕД каждым тестом. Создаем чистую тестовую базу."""
        self.test_dir = os.path.join("data")
        self.test_file = os.path.join(self.test_dir, "test_schedule.json")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Перенаправляем путь к файлу в модуле database на наш тестовый файл
        database.DATA_FILE = self.test_file
        
        # Записываем пустую структуру на 7 дней
        self.empty_data = {str(i): [] for i in range(7)}
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(self.empty_data, f)

    def tearDown(self):
        """Выполняется ПОСЛЕ каждого теста. Удаляем временный файл."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_slot_success(self):
        """Проверка успешного добавления корректного слота"""
        success, msg = database.add_slot(0, "14:00", "15:00", "Петр", "Физика")
        self.assertTrue(success)
        
        # Проверяем, что в файле действительно появилась запись
        data = database.load_schedule()
        self.assertEqual(len(data["0"]), 1)
        self.assertEqual(data["0"][0]["student"], "Петр")

    def test_invalid_time_range(self):
        """Ошибка, если время конца раньше или равно времени начала"""
        # Конец раньше начала
        success, msg = database.add_slot(0, "15:00", "14:00", "Аня", "Химия")
        self.assertFalse(success)
        
        # Время начала и конца совпадает
        success, msg = database.add_slot(0, "15:00", "15:00", "Аня", "Химия")
        self.assertFalse(success)

    def test_time_collisions(self):
        """Тестирование всевозможных наложений интервалов времени"""
        # Добавляем базовый эталонный слот: 14:00 - 15:30
        database.add_slot(0, "14:00", "15:30", "Базовый", "Мат")
        
        # Сценарий 1: Полное совпадение времени (14:00 - 15:30) -> ДОЛЖЕН БЫТЬ ОТКЛОНЕН
        success, _ = database.add_slot(0, "14:00", "15:30", "Иван", "Мат")
        self.assertFalse(success, "Разрешено полное совпадение времени")
        
        # Сценарий 2: Новый слот внутри существующего (14:15 - 15:00) -> ДОЛЖЕН БЫТЬ ОТКЛОНЕН
        success, _ = database.add_slot(0, "14:15", "15:00", "Иван", "Мат")
        self.assertFalse(success, "Разрешено наложение внутри интервала")
        
        # Сценарий 3: Наложение левым краем (13:30 - 14:30) -> ДОЛЖЕН БЫТЬ ОТКЛОНЕН
        success, _ = database.add_slot(0, "13:30", "14:30", "Иван", "Мат")
        self.assertFalse(success, "Разрешено наложение левым краем")
        
        # Сценарий 4: Наложение правым краем (15:00 - 16:00) -> ДОЛЖЕН БЫТЬ ОТКЛОНЕН
        success, _ = database.add_slot(0, "15:00", "16:00", "Иван", "Мат")
        self.assertFalse(success, "Разрешено наложение правым краем")
        
        # Сценарий 5: Новый слот полностью поглощает старый (13:00 - 17:00) -> ДОЛЖЕН БЫТЬ ОТКЛОНЕН
        success, _ = database.add_slot(0, "13:00", "17:00", "Иван", "Мат")
        self.assertFalse(success, "Разрешено поглощение интервала")

    def test_allowed_edge_cases(self):
        """Проверка работы стык-в-стык (когда уроки идут один за другим без зазора)"""
        database.add_slot(0, "14:00", "15:00", "Первый", "Мат")
        
        # Слот идет строго ДО (13:00 - 14:00) -> ДОЛЖЕН БЫТЬ РАЗРЕШЕН
        success_before, _ = database.add_slot(0, "13:00", "14:00", "Второй", "Мат")
        self.assertTrue(success_before, "Запрещен стык уроков в 14:00")
        
        # Слот идет строго ПОСЛЕ (15:00 - 16:00) -> ДОЛЖЕН БЫТЬ РАЗРЕШЕН
        success_after, _ = database.add_slot(0, "15:00", "16:00", "Третий", "Мат")
        self.assertTrue(success_after, "Запрещен стык уроков в 15:00")

    def test_delete_slot(self):
        """Проверка удаления слота"""
        database.add_slot(0, "12:00", "13:00", "Олег", "Информатика")
        data = database.load_schedule()
        slot_id = data["0"][0]["id"]
        
        # Удаляем
        database.delete_slot(0, slot_id)
        data_after = database.load_schedule()
        self.assertEqual(len(data_after["0"]), 0)

if __name__ == "__main__":
    unittest.main()
