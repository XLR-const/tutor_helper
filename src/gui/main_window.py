from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox, QInputDialog, QLineEdit, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtCore import Qt
import datetime

from src.calendar_utils import DAYS_RU, get_current_week_dates, get_current_day_index, find_nearest_slot
from src.database import load_schedule, add_slot, delete_slot, update_slot
from src.gui.day_column import DayColumn

class SlotDialog(QDialog):
    """Специальное диалоговое окно для ввода и редактирования данных слота"""
    def __init__(self, parent=None, time_start="", time_end="", student="", subject=""):
        super().__init__(parent)
        self.setWindowTitle("Данные занятия")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Поля ввода
        layout.addWidget(QLabel("Время начала (например, 15:00):"))
        self.txt_start = QLineEdit(time_start)
        layout.addWidget(self.txt_start)
        
        layout.addWidget(QLabel("Время окончания (например, 16:30):"))
        self.txt_end = QLineEdit(time_end)
        layout.addWidget(self.txt_end)
        
        layout.addWidget(QLabel("Имя ученика:"))
        self.txt_student = QLineEdit(student)
        layout.addWidget(self.txt_student)
        
        layout.addWidget(QLabel("Предмет:"))
        self.txt_subject = QLineEdit(subject)
        layout.addWidget(self.txt_subject)
        
        # Кнопки ОК / Отмена
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """Базовая проверка корректности ввода времени"""
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        
        # Проверяем формат ЧЧ:ММ
        try:
            datetime.datetime.strptime(start, "%H:%M")
            datetime.datetime.strptime(end, "%H:%M")
        except ValueError:
            QMessageBox.critical(self, "Ошибка формата", "Время должно быть в формате ЧЧ:ММ (например, 09:30, 15:00)!")
            return
            
        if not self.txt_student.text().strip() or not self.txt_subject.text().strip():
            QMessageBox.critical(self, "Ошибка заполнения", "Поля 'Ученик' и 'Предмет' не могут быть пустыми!")
            return
            
        self.accept()

    def get_data(self):
        return (
            self.txt_start.text().strip(),
            self.txt_end.text().strip(),
            self.txt_student.text().strip(),
            self.txt_subject.text().strip()
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Помогатор репетитора")
        self.resize(1100, 650) # Оптимальный размер под 7 столбцов
        
        # Центральный виджет и горизонтальная разметка для дней недели
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        
        self.columns = []
        self.setup_ui()
        self.load_and_render_data()

    def setup_ui(self):
        """Инициализирует 7 колонок дней недели"""
        dates = get_current_week_dates()
        today_idx = get_current_day_index()
        
        for i in range(7):
            is_today = (i == today_idx)
            column = DayColumn(
                day_index=i,
                day_name=DAYS_RU[i],
                day_date=dates[i],
                is_today=is_today
            )
            
            # Подключаем сигналы от колонки к обработчикам в главном окне
            column.add_requested.connect(self.on_add_slot)
            column.slot_delete_requested.connect(self.on_delete_slot)
            column.slot_edit_requested.connect(self.on_edit_slot)
            
            self.main_layout.addWidget(column)
            self.columns.append(column)

    def load_and_render_data(self):
        """Загружает данные из JSON и обновляет отображение во всех колонках"""
        schedule = load_schedule()
        today_idx = get_current_day_index()
        
        # Находим ближайший слот только для СЕГОДНЯШНЕГО дня
        slots_today = schedule.get(str(today_idx), [])
        nearest_slot_id = find_nearest_slot(slots_today)
        
        for i in range(7):
            slots_list = schedule.get(str(i), [])
            # Передаем ближайший слот только той колонке, которая является сегодняшней
            col_nearest_id = nearest_slot_id if i == today_idx else None
            self.columns[i].refresh_slots(slots_list, col_nearest_id)

    def on_add_slot(self, day_index):
        """Вызывает диалог добавления нового занятия"""
        dialog = SlotDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            t_start, t_end, student, subject = dialog.get_data()
            
            # Пытаемся сохранить в базу данных
            success, message = add_slot(day_index, t_start, t_end, student, subject)
            if success:
                self.load_and_render_data()
            else:
                # Окно ошибки Windows при наложении
                QMessageBox.critical(self, "Ошибка сохранения", message)

    def on_delete_slot(self, day_index, slot_id):
        """Удаляет слот после подтверждения"""
        reply = QMessageBox.question(
            self, 'Удаление', 'Вы уверены, что хотите удалить этот слот насовсем?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            delete_slot(day_index, slot_id)
            self.load_and_render_data()

    def on_edit_slot(self, day_index, slot_id):
        """Находит данные слота и открывает диалог редактирования"""
        schedule = load_schedule()
        slots = schedule.get(str(day_index), [])
        target_slot = next((s for s in slots if s["id"] == slot_id), None)
        
        if not target_slot:
            return
            
        dialog = SlotDialog(
            self,
            time_start=target_slot["time_start"],
            time_end=target_slot["time_end"],
            student=target_slot["student"],
            subject=target_slot["subject"]
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            t_start, t_end, student, subject = dialog.get_data()
            
            success, message = update_slot(day_index, slot_id, t_start, t_end, student, subject)
            if success:
                self.load_and_render_data()
            else:
                QMessageBox.critical(self, "Ошибка изменения", message)
