from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

class SlotWidget(QWidget):
    # Сигналы для связи с главным окном при нажатии на кнопки
    delete_requested = pyqtSignal(str) # Передает id слота
    edit_requested = pyqtSignal(str)   # Передает id слота

    def __init__(self, slot_data, is_nearest=False, parent=None):
        super().__init__(parent)
        self.slot_id = slot_data["id"]
        self.slot_data = slot_data
        
        # Основной вертикальный слой
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(4)
        
        # Текстовая информация (Время, Ученик, Предмет)
        time_text = f"⏰ {slot_data['time_start']} - {slot_data['time_end']}"
        student_text = f"👤 {slot_data['student']}"
        subject_text = f"📚 {slot_data['subject']}"
        
        self.lbl_time = QLabel(time_text)
        self.lbl_time.setStyleSheet("font-weight: bold; color: #333333;")
        self.lbl_student = QLabel(student_text)
        self.lbl_subject = QLabel(subject_text)
        self.lbl_subject.setStyleSheet("color: #666666; font-size: 11px;")
        
        self.main_layout.addWidget(self.lbl_time)
        self.main_layout.addWidget(self.lbl_student)
        self.main_layout.addWidget(self.lbl_subject)
        
        # Контейнер для кнопок управления (по умолчанию скрыт)
        self.action_container = QWidget()
        self.action_layout = QHBoxLayout(self.action_container)
        self.action_layout.setContentsMargins(0, 4, 0, 0)
        self.action_layout.setSpacing(6)
        
        self.btn_edit = QPushButton("✏️ Изменить")
        self.btn_delete = QPushButton("❌ Удалить")
        
        # Стили кнопок управления
        self.btn_edit.setStyleSheet("font-size: 11px; padding: 3px; background-color: #e0e0e0; border-radius: 3px;")
        self.btn_delete.setStyleSheet("font-size: 11px; padding: 3px; background-color: #ffcccc; color: #cc0000; border-radius: 3px;")
        
        self.action_layout.addWidget(self.btn_edit)
        self.action_layout.addWidget(self.btn_delete)
        
        self.main_layout.addWidget(self.action_container)
        self.action_container.hide() # Прячем кнопки при создании
        
        # Подключаем события кнопок
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.slot_id))
        self.btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.slot_id))
        
        # Задаем базовый стиль карточки занятия
        self.set_card_style(is_nearest)

    def set_card_style(self, is_nearest):
        """Определяет внешний вид карточки слота"""
        if is_nearest:
            # Выделение ближайшего будущего или текущего слота (нежно-красный фон и сочная красная рамка)
            bg_color = "#fff5f5"      # Мягкий красный оттенок фона
            border_color = "#e63946"  # Насыщенный красный цвет рамки-маркера
            text_style = "font-weight: bold; color: #b7094c;" # Темно-красный текст для времени
            border_width = "2px"      # Делаем рамку чуть толще, чтобы выделить слот
        else:
            # Обычный слот
            bg_color = "#f8f9fa"
            border_color = "#e5e5e5"
            text_style = "font-weight: bold; color: #333333;"
            border_width = "1px"
            
        self.setStyleSheet(f"""
            SlotWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 6px; /* Закругленные углы прямоугольника */
            }}
            SlotWidget:hover {{
                border-color: #0078d7;
                background-color: #ffffff;
            }}
        """)
        self.lbl_time.setStyleSheet(text_style)


    def mousePressEvent(self, event):
        """Перехват клика мыши: показываем или скрываем меню кнопок"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.action_container.isVisible():
                self.action_container.hide()
            else:
                self.action_container.show()
        super().mousePressEvent(event)
