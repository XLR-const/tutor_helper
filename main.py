import sys
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config import GLOBAL_STYLE

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()