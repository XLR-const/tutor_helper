from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QMessageBox, 
                             QInputDialog, QLineEdit, QDialog, QVBoxLayout, 
                             QLabel, QDialogButtonBox, QSystemTrayIcon, QMenu, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import datetime
import sys
import os
import winreg

from src.calendar_utils import DAYS_RU, get_current_week_dates, get_current_day_index, find_nearest_slot, time_to_minutes
from src.database import load_schedule, add_slot, delete_slot, update_slot
from src.gui.day_column import DayColumn
from src.export_utils import save_grid_to_png

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
        self.resize(1150, 700) # Чуть увеличили размер, чтобы кнопка сверху не сжимала дни
        
        # 1. Основной вертикальный контейнер для всего окна
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.window_layout = QVBoxLayout(self.central_widget)
        self.window_layout.setContentsMargins(10, 10, 10, 10)
        self.window_layout.setSpacing(6)
        
        # 2. СОЗДАЕМ ВЕРХНЮЮ ПАНЕЛЬ ДЛЯ КНОПКИ ЭКСПОРТА
        self.top_panel = QWidget()
        self.top_layout = QHBoxLayout(self.top_panel)
        self.top_layout.setContentsMargins(4, 0, 4, 4)
        
        self.btn_export_png = QPushButton("📸 Сохранить расписание как фото (PNG)")
        self.btn_export_png.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_png.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                color: #00bcd4;
                border: 1px solid #00bcd4;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00bcd4;
                color: #121212;
            }
        """)
        # Подключаем клик кнопки к методу (его мы добавим следующим шагом)
        self.btn_export_png.clicked.connect(self.export_to_png)
        self.top_layout.addWidget(self.btn_export_png, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Добавляем верхнюю панель в самый верх окна
        self.window_layout.addWidget(self.top_panel)
        
        # 3. ВАША СЕТКА ДНЕЙ НЕДЕЛИ (теперь она живет внутри отдельного виджета под кнопкой)
        self.grid_widget = QWidget()
        self.main_layout = QHBoxLayout(self.grid_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)
        
        # Кладем сетку дней под кнопку и заставляем её растягиваться на всё свободное место
        self.window_layout.addWidget(self.grid_widget, stretch=1)
        
        # 4. Ваш оригинальный код настроек и таймеров (остался полностью без изменений)
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
        """Инициализация иконки в системном трее из внутренних ресурсов сборки"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Проверяем, запущена ли скомпилированная программа
        if getattr(sys, 'frozen', False):
            # PyInstaller распаковывает ресурсы во временную папку _MEIPASS
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # Если запускаем как обычный скрипт .py
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        icon_path = os.path.join(base_dir, "tutor_helper.ico")
        
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # На всякий случай: если файл не найден, берем системный значок, чтобы трей не упал
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        
        tray_menu = QMenu()
        
        action_show = tray_menu.addAction("Открыть Помогатор")
        action_show.triggered.connect(self.show_normal_and_raise)
        
        tray_menu.addSeparator()
        
        # НОВАЯ ГАЛОЧКА: Автозагрузка с Windows
        self.action_autostart = tray_menu.addAction("⚙️ Автозагрузка с Windows")
        self.action_autostart.setCheckable(True)
        # Проверяем при старте, прописана ли уже программа в реестре, и ставим галочку
        self.action_autostart.setChecked(self.check_autostart_registry())
        self.action_autostart.triggered.connect(self.toggle_autostart)
        
        action_clear = tray_menu.addAction("🧹 Очистить всю неделю")
        action_clear.triggered.connect(self.on_clear_all_week_click)
        
        tray_menu.addSeparator()
        
        action_exit = tray_menu.addAction("Выйти из программы")
        action_exit.triggered.connect(self.force_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def check_autostart_registry(self):
        """Проверяет в реестре Windows, включен ли автозапуск для приложения"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            # Ищем ключ с именем "TutorAssistant"
            value, _ = winreg.QueryValueEx(key, "TutorAssistant")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_autostart(self, checked):
        """Включает или выключает автозапуск программы в реестре Windows"""
        # Определяем путь к запущенному файлу
        # Если запущена сборка .exe, sys.frozen будет True, иначе это обычный .py скрипт
        is_exe = getattr(sys, 'frozen', False)
        
        if not is_exe:
            QMessageBox.warning(
                self, "Автозагрузка", 
                "Запись в реестр доступна только для скомпилированного .exe файла!\n"
                "Скрипты .py не могут быть добавлены в автозапуск напрямую."
            )
            self.action_autostart.setChecked(False)
            return

        # Получаем полный абсолютный путь к вашему .exe файлу
        exe_path = os.path.abspath(sys.argv[0])
        
        # Модифицируем путь, чтобы программа запускалась в свернутом режиме (флаг --minimized)
        # Для этого в будущем можно будет дописать логику, но пока просто прописываем путь
        registry_value = f'"{exe_path}"'

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            
            if checked:
                # Записываем ключ в реестр
                winreg.SetValueEx(key, "TutorAssistant", 0, winreg.REG_SZ, registry_value)
                self.tray_icon.showMessage(
                    "Автозагрузка включена",
                    "Помогатор теперь будет автоматически запускаться при включении компьютера.",
                    QSystemTrayIcon.MessageIcon.Information, 2000
                )
            else:
                # Удаляем ключ из реестра
                try:
                    winreg.DeleteValue(key, "TutorAssistant")
                    self.tray_icon.showMessage(
                        "Автозагрузка выключена",
                        "Программа успешно удалена из автозапуска Windows.",
                        QSystemTrayIcon.MessageIcon.Information, 2000
                    )
                except KeyError:
                    pass
                    
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка реестра", f"Не удалось изменить настройки автозапуска: {e}")
            self.action_autostart.setChecked(not checked) # Возвращаем галочку назад при сбое


    def on_clear_all_week_click(self):
        """Слот обработки клика полной очистки базы данных"""
        reply = QMessageBox.question(
            self, '⚠️ Опасная зона', 
            'Вы уверены, что хотите ПОЛНОСТЬЮ СТЕРЕТЬ расписание и Green Line на все дни недели?\nВосстановить данные будет невозможно!',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.database import clear_all_weeks
            if clear_all_weeks():
                self.load_and_render_data() # Мгновенно обновляем интерфейс (сетка станет чистой)
                QMessageBox.information(self, "Успех", "База данных успешно очищена!")


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
        """Фоновый алгоритм: уведомляет один раз за 1 час и один раз за 10 минут до урока"""
        schedule = load_schedule()
        today_idx = get_current_day_index()
        day_today_data = schedule.get(str(today_idx), {"green_line": None, "slots": []})
        slots_today = day_today_data.get("slots", [])
        
        if not slots_today or not isinstance(slots_today, list):
            return
            
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        for slot in slots_today:
            if not isinstance(slot, dict) or "time_start" not in slot:
                continue
                
            try:
                start_minutes = time_to_minutes(slot["time_start"])
                time_diff = start_minutes - current_minutes
                
                # Проверяем две конкретные временные зоны
                is_hourly_alert = (58 <= time_diff <= 60)
                is_ten_min_alert = (8 <= time_diff <= 10)
                
                if is_hourly_alert or is_ten_min_alert:
                    # Создаем уникальный ключ для памяти (например: "id_60" или "id_10")
                    alert_type = "60" if is_hourly_alert else "10"
                    notification_key = f"{slot['id']}_{alert_type}"
                    
                    if notification_key not in self.notified_slots:
                        self.notified_slots.add(notification_key)
                        
                        # Звуковой сигнал
                        from PyQt6.QtWidgets import QApplication
                        QApplication.beep()
                        
                        # Подбираем текст в зависимости от времени
                        title = "⏳ Занятие через час!" if is_hourly_alert else "🚨 Занятие скоро начнется!"
                        body = f"Через {int(time_diff)} мин. урок: {slot['student']}\nПредмет: {slot['subject']}"
                        
                        # Выводим нативное окно
                        self.tray_icon.showMessage(
                            title,
                            body,
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
            
    def export_to_png(self):
        """Вызывает изолированную внешнюю функцию для создания снимка экрана"""
        save_grid_to_png(self, self.grid_widget, self.columns)


