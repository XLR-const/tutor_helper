import os

# Описываем структуру: ключи — это папки, значения — списки файлов в них
STRUCTURE = {
    "data": ["schedule.json"],
    "src": ["__init__.py", "config.py", "database.py", "calendar_utils.py"],
    "src/gui": ["__init__.py", "main_window.py", "day_column.py", "slot_widget.py"],
    "": ["main.py", "requirements.txt"]  # Файлы в корне проекта
}

def create_project_structure():
    print("🚀 Начинаю создание структуры проекта tutor_helper...\n")
    
    for folder, files in STRUCTURE.items():
        # Если это не корень, создаем папку
        if folder:
            os.makedirs(folder, exist_ok=True)
            print(f"📁 Создана папка: {folder}")
        
        # Создаем файлы внутри папки
        for file in files:
            file_path = os.path.join(folder, file) if folder else file
            
            # Проверяем, чтобы случайно не перезаписать уже существующий файл
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    # Запишем базовый контент в файлы настроек и зависимостей
                    if file == "requirements.txt":
                        f.write("PyQt6==6.6.1\n")
                    elif file == "schedule.json":
                        f.write('{\n  "0": [],\n  "1": [],\n  "2": [],\n  "3": [],\n  "4": [],\n  "5": [],\n  "6": []\n}')
                    else:
                        f.write("") # Создаем пустой файл
                print(f"  📄 Создан файл: {file_path}")
            else:
                print(f"  ⚠️ Файл уже существует, пропускаю: {file_path}")

    print("\n✅ Структура успешно создана! Файл schedule.json базово инициализирован.")

if __name__ == "__main__":
    create_project_structure()
