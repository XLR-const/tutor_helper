from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

class SlotWidget(QWidget):
    delete_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)

    def __init__(self, slot_data, is_nearest=False, parent=None):
        super().__init__(parent)
        self.slot_id = slot_data["id"]
        self.slot_data = slot_data
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Все элементы прижаты к верху
        
        # Данные слота
        time_text = f"⏰ {slot_data['time_start']} - {slot_data['time_end']}"
        student_text = f"👤 {slot_data['student']}"
        subject_text = f"📚 {slot_data['subject']}"
        
        self.lbl_time = QLabel(time_text)
        self.lbl_student = QLabel(student_text)
        self.lbl_student.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.lbl_subject = QLabel(subject_text)
        self.lbl_subject.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        
        self.main_layout.addWidget(self.lbl_time)
        self.main_layout.addWidget(self.lbl_student)
        self.main_layout.addWidget(self.lbl_subject)
        
        # Контейнер для кнопок управления
        self.action_container = QWidget()
        self.action_layout = QHBoxLayout(self.action_container)
        self.action_layout.setContentsMargins(0, 4, 0, 0)
        self.action_layout.setSpacing(6)
        
        self.btn_edit = QPushButton("✏️")
        self.btn_delete = QPushButton("❌")
        
        # Жестко фиксируем геометрию только кнопок, чтобы они не сжимались
        self.btn_edit.setFixedHeight(24)
        self.btn_edit.setMinimumWidth(45)
        self.btn_delete.setFixedHeight(24)
        self.btn_delete.setMinimumWidth(45)
        
        self.btn_edit.setStyleSheet("""
            QPushButton {
                font-size: 11px; 
                background-color: #3d3d3d; 
                border: 1px solid #555555; 
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton:hover { background-color: #4d4d4d; border-color: #0078d7; }
        """)
        
        self.btn_delete.setStyleSheet("""
            QPushButton {
                font-size: 11px; 
                background-color: #442222; 
                color: #ff8888; 
                border: 1px solid #663333; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #552222; border-color: #ff4d6d; }
        """)
        
        self.action_layout.addWidget(self.btn_edit)
        self.action_layout.addWidget(self.btn_delete)
        
        self.main_layout.addWidget(self.action_container)
        self.action_container.hide() # По умолчанию скрываем кнопки
        
        self.btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.slot_id))
        self.btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.slot_id))
        
        self.set_card_style(is_nearest)

    def set_card_style(self, is_nearest):
        if is_nearest:
            bg_color = "#2c1619"      
            border_color = "#ff4d6d"  
            text_style = "font-weight: bold; color: #ff758f; font-size: 13px;" 
            border_width = "2px"      
        else:
            bg_color = "#2d2d2d"
            border_color = "#3d3d3d"
            text_style = "font-weight: bold; color: #00bcd4; font-size: 12px;" 
            border_width = "1px"
            
        self.setStyleSheet(f"""
            SlotWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 6px;
            }}
            SlotWidget:hover {{
                border-color: #0078d7;
                background-color: #333333;
            }}
        """)
        self.lbl_time.setStyleSheet(text_style)

    def mousePressEvent(self, event):
        """Перехват клика мыши: динамически меняем размер карточки при открытии меню"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.action_container.isVisible():
                self.action_container.hide()
            else:
                self.action_container.show()
            
            # ВАЖНО: Принудительно просим карточку пересчитать свою высоту под новые элементы
            self.adjustSize()
            
        super().mousePressEvent(event)
