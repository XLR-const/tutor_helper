# Глобальные стили для элегантной ТЁМНОЙ темы (QSS)
GLOBAL_STYLE = """
/* Главное окно и диалоги */
QMainWindow, QDialog {
    background-color: #121212;
    color: #ffffff;
}

/* Настройки текста */
QLabel {
    font-family: "Segoe UI", -apple-system, Arial, sans-serif;
    font-size: 12px;
    color: #e0e0e0;
}

/* Поля ввода в диалоговых окнах */
QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #0078d7;
}

/* Системные кнопки в диалогах */
QPushButton {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #3d3d3d;
    border-color: #0078d7;
}
QPushButton:pressed {
    background-color: #1e1e1e;
}

/* Стили для стандартной ОБЫЧНОЙ колонки дня недели */
.DayColumn {
    background-color: #1e1e1e;
    border-right: 1px solid #2d2d2d;   /* Стильный вертикальный разделитель */
    border-top: 1px solid #1a1a1a;
    border-bottom: 1px solid #1a1a1a;
    border-left: none;
    border-radius: 0px;
}

/* Стили для СЕГОДНЯШНЕЙ колонки (неоновый синий акцент) */
.DayColumn[today="true"] {
    background-color: #1a233a;          /* Глубокий темно-синий фон */
    border: 2px solid #0078d7;          /* Яркая неоновая рамка */
    border-radius: 8px;
}
"""
