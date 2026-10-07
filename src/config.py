# Глобальные стили для элементов приложения (QSS)
GLOBAL_STYLE = """
QMainWindow {
    background-color: #ffffff;
}
QLabel {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QInputDialog, QMessageBox, QDialog {
    background-color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
}
QPushButton {
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Стили для обычного столбца дня недели (создает вертикальные разделители) */
.DayColumn {
    background-color: #ffffff;
    border-right: 1px solid #dcdcdc; /* Тонкая серая линия справа — разделитель */
    border-top: 1px solid #f0f0f0;
    border-bottom: 1px solid #f0f0f0;
    border-left: none;
    border-radius: 0px;
}

/* Стили для СЕГОДНЯШНЕГО столбца (выделение цветом и рамкой) */
.DayColumn[today="true"] {
    background-color: #f0f7ff; /* Приятный мягкий синеватый фон */
    border: 2px solid #0078d7;  /* Яркая синяя рамка вокруг всего дня */
    border-radius: 6px;
}
"""
