import logging
import sys
from pathlib import Path

# Создаём папку для логов
Path("logs").mkdir(exist_ok=True)

# Настройка форматирования
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Корневой логгер
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Обработчик для файла
file_handler = logging.FileHandler("logs/sokrat.log", encoding='utf-8')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Обработчик для консоли
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Функция для получения логгера
def get_logger(name):
    return logging.getLogger(name)
