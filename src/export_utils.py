import datetime
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt

def save_grid_to_png(parent_window, grid_widget, columns_list):
    """
    Изолированный модуль для создания графического снимка сетки расписания.
    Временно скрывает кнопки управления, делает скриншот и сохраняет файл.
    """
    # 1. Скрываем служебные интерфейсные кнопки во всех колонках
    for col in columns_list:
        col.btn_green_line.hide()
        col.btn_add.hide()
        
    # Заставляем движок PyQt6 мгновенно перерисовать интерфейс без кнопок
    QApplication.processEvents()
    
    try:
        # 2. Захватываем изображение виджета сетки в память
        pixmap = grid_widget.grab()
        
        # Формируем имя файла с актуальной датой
        filename = f"Расписание_недели_{datetime.date.today().strftime('%d.%m.%Y')}.png"
        
        # 3. Сохраняем картинку на диск
        if pixmap.save(filename, "PNG"):
            QMessageBox.information(
                parent_window, "Успешный экспорт", 
                f"Расписание успешно сохранено в файл:\n{filename}\n\nВы можете отправить его ученикам!"
            )
        else:
            QMessageBox.critical(parent_window, "Ошибка", "Не удалось сохранить файл изображения.")
            
    except Exception as e:
        QMessageBox.critical(parent_window, "Ошибка экспорта", f"Произошел сбой при создании снимка: {e}")
        
    finally:
        # 4. В любом случае возвращаем кнопки управления обратно на экран
        for col in columns_list:
            col.btn_green_line.show()
            col.btn_add.show()
