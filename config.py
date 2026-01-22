"""
Модуль для работы с конфигурацией приложения.
Управляет загрузкой переменных окружения и определением путей к файлам данных.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


def get_app_data_dir() -> Path:
    """
    Получить путь к папке данных приложения в пользовательской директории.
    Используется для хранения файлов, которые требуют записи (БД, логи, настройки).
    
    Returns:
        Path к папке данных приложения
    """
    if sys.platform == "win32":
        # Windows: используем LOCALAPPDATA (локальные данные пользователя)
        app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        # Linux/Mac: используем домашнюю директорию
        app_data = os.path.expanduser("~")
    
    app_dir = Path(app_data) / "ChatList"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def load_env_file():
    """
    Загрузить переменные окружения из .env файла.
    Ищет .env в следующем порядке:
    1. Пользовательская папка данных (приоритет)
    2. Папка установки приложения
    3. Текущая директория (для разработки)
    """
    # Список путей для поиска .env файла
    env_paths = [
        get_app_data_dir() / ".env",  # Пользовательская папка данных
        Path(sys.executable).parent / ".env" if hasattr(sys, 'frozen') else None,  # Папка установки (только для exe)
        Path.cwd() / ".env",  # Текущая директория
    ]
    
    # Убираем None значения
    env_paths = [p for p in env_paths if p is not None]
    
    # Загружаем .env из первого найденного пути
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path), override=True)
            return
    
    # Если .env не найден, загружаем из текущей директории (стандартное поведение)
    load_dotenv()


# Автоматически загружаем .env при импорте модуля
load_env_file()

