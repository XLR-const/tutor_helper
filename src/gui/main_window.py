from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QMessageBox, 
                             QInputDialog, QLineEdit, QDialog, QVBoxLayout, 
                             QLabel, QDialogButtonBox, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import datetime
import os

from src.calendar_utils import DAYS_RU, get_current_week_dates, get_current_day_index, find_nearest_slot, time_to_minutes
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
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        
        try:
            datetime.datetime.strptime(start, "%H:%M")
            datetime.datetime.strptime(end, "%H:%M")
        except ValueError:
            QMessageBox.critical(self, "Ошибка формата", "Время должно быть в формате ЧЧ:ММ!")
            return
            
        if not self.txt_student.text().strip() or not self.txt_subject.text().strip():
            QMessageBox.critical(self, "Ошибка заполнения", "Поля не могут быть пустыми!")
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
        self.resize(1100, 650)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        
        self.columns = []
        self.setup_ui()
        self.load_and_render_data()
        
        # Настройка фонового трея и уведомлений
        self.setup_tray()
        
        # Список уже отправленных уведомлений, чтобы не спамить каждую секунду в течение этой минуты
        self.notified_slots = set()
        
        # Таймер фоновой проверки времени (работает раз в 30 секунд)
        self.bg_timer = QTimer(self)
        self.bg_timer.timeout.connect(self.check_upcoming_notifications)
        self.bg_timer.start(30000)

    def setup_ui(self):
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
            column.add_requested.connect(self.on_add_slot)
            column.slot_delete_requested.connect(self.on_delete_slot)
            column.slot_edit_requested.connect(self.on_edit_slot)
            
            column.green_line_changed.connect(self.on_green_line_changed)

            
            self.main_layout.addWidget(column)
            self.columns.append(column)

    def load_and_render_data(self):
        """Загружает данные из JSON и обновляет отображение во всех колонках"""
        schedule = load_schedule()
        today_idx = get_current_day_index()
        
        # Извлекаем слоты для расчета ближайшего урока
        day_today_data = schedule.get(str(today_idx), {"green_line": None, "slots": []})
        slots_today = day_today_data.get("slots", [])
        nearest_slot_id = find_nearest_slot(slots_today)
        
        for i in range(7):
            day_data = schedule.get(str(i), {"green_line": None, "slots": []})
            col_nearest_id = nearest_slot_id if i == today_idx else None
            # Передаем весь словарь дня (слоты + границу)
            self.columns[i].refresh_slots(day_data, col_nearest_id)


    def setup_tray(self):
        """Инициализация иконки в системном трее Windows"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Загружаем ту же иконку, что лежит в корне проекта
        icon_path = "tutor_helper.ico"
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # Контекстное меню при клике правой кнопкой мыши по значку в трее
        tray_menu = QMenu()
        action_show = tray_menu.addAction("Открыть Помогатор")
        action_show.triggered.connect(self.show_normal_and_raise)
        
        action_exit = tray_menu.addAction("Выйти из программы")
        action_exit.triggered.connect(self.force_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Клик левой кнопкой мыши открывает окно
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Показываем иконку в скрытых значках
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal_and_raise()

    def show_normal_and_raise(self):
        """Красиво разворачивает окно поверх других окон"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """Перехват закрытия окна: прячем в трей вместо завершения процесса"""
        if self.tray_icon.isVisible():
            self.hide()
            # Показываем маленькую подсказку над часами, что приложение не закрылось
            self.tray_icon.showMessage(
                "Помогатор репетитора",
                "Приложение свернуто в фоновый режим и следит за расписанием.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore() # Блокируем уничтожение окна

    def force_exit(self):
        """Метод для полного закрытия программы из контекстного меню трея"""
        self.tray_icon.hide()
        QTimer.singleShot(0, self.close)
        # Насильно завершаем процесс
        import sys
        sys.exit(0)

    def check_upcoming_notifications(self):
        """Фоновый алгоритм: ищет слоты на сегодня, до которых осталось ровно 60 минут"""
        schedule = load_schedule()
        today_idx = get_current_day_index()
        day_today_data = schedule.get(str(today_idx), {"green_line": None, "slots": []})
        slots_today = day_today_data.get("slots", [])
        
        if not slots_today or not isinstance(slots_today, list):
            return
            
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        for slot in slots_today:
            # Защита от некорректных типов данных внутри слота
            if not isinstance(slot, dict) or "time_start" not in slot:
                continue
                
            try:
                start_minutes = time_to_minutes(slot["time_start"])
                time_diff = start_minutes - current_minutes
                
                if 0 <= time_diff <= 60 and slot["id"] not in self.notified_slots:
                    self.notified_slots.add(slot["id"])
                    
                    from PyQt6.QtWidgets import QApplication
                    QApplication.beep()
                    
                    self.tray_icon.showMessage(
                        "⏳ Скоро занятие!",
                        f"Через {int(time_diff)} мин. урок: {slot['student']}\nПредмет: {slot['subject']}",
                        QSystemTrayIcon.MessageIcon.Information,
                        10000
                    )
            except Exception as e:
                print(f"Ошибка обработки фонового слота: {e}")



    # Методы кнопок добавления/удаления (остаются прежними, но с обновлением интерфейса)
    def on_add_slot(self, day_index):
        dialog = SlotDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            t_start, t_end, student, subject = dialog.get_data()
            success, message = add_slot(day_index, t_start, t_end, student, subject)
            if success:
                self.load_and_render_data()
            else:
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
        """Находит данные слота с учетом новой структуры и открывает диалог редактирования"""
        schedule = load_schedule()
        
        # Безопасно извлекаем словарь дня и список его слотов
        day_data = schedule.get(str(day_index), {"green_line": None, "slots": []})
        slots = day_data.get("slots", [])
        
        # Ищем нужный слот по ID
        target_slot = None
        for s in slots:
            if isinstance(s, dict) and s.get("id") == slot_id:
                target_slot = s
                break
        
        if not target_slot:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти данные занятия для редактирования!")
            return
            
        # Открываем форму с уже заполненными старыми данными
        dialog = SlotDialog(
            self,
            time_start=target_slot.get("time_start", ""),
            time_end=target_slot.get("time_end", ""),
            student=target_slot.get("student", ""),
            subject=target_slot.get("subject", "")
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            t_start, t_end, student, subject = dialog.get_data()
            
            # Сохраняем обновленные данные в базу
            success, message = update_slot(day_index, slot_id, t_start, t_end, student, subject)
            if success:
                self.load_and_render_data()
            else:
                QMessageBox.critical(self, "Ошибка изменения", message)

                
    def on_green_line_changed(self, day_index, time_str):
        """Обрабатывает установку или удаление границы личных дел"""
        from src.database import set_green_line
        success, message = set_green_line(day_index, time_str)
        if success:
            self.load_and_render_data()
        else:
            QMessageBox.critical(self, "Ошибка Green Line", message)

