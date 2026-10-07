from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt
from src.gui.slot_widget import SlotWidget

class DayColumn(QWidget):
    # Сигнал отправляется, когда нажата кнопка "+" внизу столбца
    add_requested = pyqtSignal(int)      # Передает индекс дня недели
    slot_delete_requested = pyqtSignal(int, str) # Передает индекс дня и id слота
    slot_edit_requested = pyqtSignal(int, str)   # Передает индекс дня и id слота

    def __init__(self, day_index, day_name, day_date, is_today=False, parent=None):
        super().__init__(parent)
        self.day_index = day_index
        
        # Главный вертикальный слой колонки
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(8)
        
        # 1. Заголовок дня недели и даты
        self.lbl_title = QLabel(f"{day_name}\n({day_date})")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #222222; padding: 4px;")
        self.main_layout.addWidget(self.lbl_title)
        
        # 2. Область прокрутки для слотов, если их станет слишком много
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        # Контейнер внутри прокрутки, куда складываются слоты
        self.slots_container = QWidget()
        self.slots_layout = QVBoxLayout(self.slots_container)
        self.slots_layout.setContentsMargins(0, 0, 0, 0)
        self.slots_layout.setSpacing(6)
        self.slots_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Все слоты прижимаются к верху
        
        self.scroll_area.setWidget(self.slots_container)
        self.main_layout.addWidget(self.scroll_area)
        
        # 3. Круглая кнопка "+" для добавления слотов
        self.btn_add = QPushButton("⊕")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setToolTip("Добавить новый слот времени")
        self.btn_add.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                color: #0078d7;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                color: #005a9e;
                font-size: 26px;
            }
        """)
        self.btn_add.clicked.connect(lambda: self.add_requested.emit(self.day_index))
        self.main_layout.addWidget(self.btn_add, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Настраиваем подсветку "Сегодня"
        self.set_column_style(is_today)

    def set_column_style(self, is_today):
        """Задает свойства для стилизации столбца через QSS"""
        # Заставляем виджет корректно отображать фоновые стили QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Используем специальное динамическое свойство для QSS
        if is_today:
            self.setProperty("today", "true")
            self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d7; padding: 4px; background: transparent;")
        else:
            self.setProperty("today", "false")
            self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #222222; padding: 4px; background: transparent;")
        
        # Обновляем стиль виджета в реальном времени
        self.style().unpolish(self)
        self.style().polish(self)


    def refresh_slots(self, slots_list, nearest_slot_id):
        """Очищает старые слоты в колонке и отрисовывает обновленный список из JSON"""
        # Удаляем старые виджеты слотов из разметки
        while self.slots_layout.count():
            item = self.slots_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Создаем новые виджеты для каждого занятия
        for slot in slots_list:
            is_nearest = (slot["id"] == nearest_slot_id)
            slot_widget = SlotWidget(slot, is_nearest=is_nearest)
            
            # Пробрасываем сигналы кнопок наружу в главное окно через эту колонку
            slot_widget.delete_requested.connect(lambda s_id: self.slot_delete_requested.emit(self.day_index, s_id))
            slot_widget.edit_requested.connect(lambda s_id: self.slot_edit_requested.emit(self.day_index, s_id))
            
            self.slots_layout.addWidget(slot_widget)
