from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from src.gui.slot_widget import SlotWidget
from src.calendar_utils import time_to_minutes

class DayColumn(QWidget):
    add_requested = pyqtSignal(int)
    slot_delete_requested = pyqtSignal(int, str)
    slot_edit_requested = pyqtSignal(int, str)
    green_line_changed = pyqtSignal(int, str)

    def __init__(self, day_index, day_name, day_date, is_today=False, parent=None):
        super().__init__(parent)
        self.day_index = day_index
        self.setMinimumWidth(150)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        
        # 1. Заголовок дня
        self.lbl_title = QLabel(f"{day_name}\n({day_date})")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.lbl_title)
        
        # 2. Главная рабочая область дня (вертикальный слой для элементов)
        self.timeline_area = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_area)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(6)
        self.timeline_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Все элементы прижимаются к верху
        self.main_layout.addWidget(self.timeline_area, stretch=1)
        
        # 3. Кнопка установки Green Line 🟢
        self.btn_green_line = QPushButton("🟢")
        self.btn_green_line.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_green_line.setToolTip("Задать границу личных дел (Green Line)")
        self.btn_green_line.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        self.btn_green_line.clicked.connect(self.on_set_green_line_click)
        self.main_layout.addWidget(self.btn_green_line, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 4. Круглая кнопка "+" для уроков
        self.btn_add = QPushButton("⊕")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet("""
            QPushButton { font-size: 24px; color: #00bcd4; background-color: transparent; border: none; }
            QPushButton:hover { color: #00e5ff; font-size: 26px; }
        """)
        self.btn_add.clicked.connect(lambda: self.add_requested.emit(self.day_index))
        self.main_layout.addWidget(self.btn_add, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.set_column_style(is_today)

    def set_column_style(self, is_today):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if is_today:
            self.setProperty("today", "true")
            self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d7; padding: 6px; background: transparent;")
        else:
            self.setProperty("today", "false")
            self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff; padding: 6px; background: transparent;")
        self.style().unpolish(self)
        self.style().polish(self)

    def on_set_green_line_click(self):
        """Вызывает диалог ввода времени для границы личных дел"""
        time_str, ok = QInputDialog.getText(
            self, "Green Line", 
            "Введите время окончания личных дел (ЧЧ:ММ)\nОставьте пустым, чтобы УДАЛИТЬ границу:",
            text="12:00"
        )
        if ok:
            # Если пользователь нажал ОК, передаем введенное значение (или пустую строку для удаления)
            self.green_line_changed.emit(self.day_index, time_str.strip())

    def refresh_slots(self, day_data, nearest_slot_id):
        """Очищает старую разметку и строит плотную, красивую шкалу дня без пустых зазоров"""
        # 1. Полностью очищаем все старые виджеты из timeline
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
                
        green_line_time = day_data.get("green_line")
        slots_list = day_data.get("slots", [])
        
        # Задаем жесткий фиксированный шаг между карточками в 4 пикселя
        self.timeline_layout.setSpacing(4)
        
        # 2. Если у этого дня задана Green Line — создаем компактную утреннюю зону
        if green_line_time:
            try:
                # Создаем карточку зеленой зоны специально для этого дня
                green_zone_widget = QWidget()
                green_zone_widget.setMinimumHeight(50)
                green_zone_widget.setMaximumHeight(80) # Ограничиваем высоту, чтобы она не выталкивала слоты вниз
                green_zone_widget.setStyleSheet("""
                    background-color: rgba(43, 147, 72, 0.12);
                    border: 1px dashed #2b9348;
                    border-radius: 6px;
                """)
                
                gz_layout = QVBoxLayout(green_zone_widget)
                gz_layout.setContentsMargins(4, 4, 4, 4)
                
                lbl_green = QLabel(f"Личное время\nдо {green_line_time}")
                lbl_green.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_green.setStyleSheet("color: #2b9348; font-weight: bold; font-size: 11px; background: transparent;")
                gz_layout.addWidget(lbl_green)
                
                # Создаем уникальную разделительную линию
                green_line_divider = QWidget()
                green_line_divider.setFixedHeight(2)
                green_line_divider.setStyleSheet("background-color: #2b9348; border-radius: 1px;")
                
                # Добавляем зеленую зону в начало timeline со стандартным весом 0
                self.timeline_layout.addWidget(green_zone_widget, stretch=0)
                self.timeline_layout.addWidget(green_line_divider)
            except Exception as e:
                print(f"Ошибка отрисовки Green Line: {e}")
                
        # 3. Отрисовываем обычные слоты учеников ниже зеленой черты
        for slot in slots_list:
            is_nearest = (slot["id"] == nearest_slot_id)
            slot_widget = SlotWidget(slot, is_nearest=is_nearest)
            
            slot_widget.delete_requested.connect(lambda s_id: self.slot_delete_requested.emit(self.day_index, s_id))
            slot_widget.edit_requested.connect(lambda s_id: self.slot_edit_requested.emit(self.day_index, s_id))
            
            # Добавляем виджет без растяжения (stretch=0), чтобы он был аккуратным и плотным
            self.timeline_layout.addWidget(slot_widget, stretch=0)
            
        # 4. СЕКРЕТНЫЙ ИСПРАВЛЯЮЩИЙ ШАГ: Добавляем пустой пружинный stretch в самый конец.
        # Он заберет на себя ВСЁ лишнее пустое пространство внизу столбца и прижмет карточки друг к другу.
        self.timeline_layout.addStretch(1)
