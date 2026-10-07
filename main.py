import sys
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config import GLOBAL_STYLE

def main():
    # Создаем экземпляр приложения
    app = QApplication(sys.argv)
    
    # Применяем оформление
    app.setStyleSheet(GLOBAL_STYLE)
    
    # Создаем и отображаем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл событий приложения
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
