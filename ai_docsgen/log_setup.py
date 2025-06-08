import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from colorama import Fore, Style, init

from ai_docsgen.config import settings

# Инициализация colorama
init(autoreset=True)

# Создание директории для логов, если она не существует
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Имя файла лога с текущей датой
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")

# Цвета для разных уровней логирования
LOG_COLORS = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.MAGENTA + Style.BRIGHT
}


# Класс форматтера с цветами для консоли
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Сохраняем исходное имя уровня
        levelname = record.levelname
        # Применяем цвет если уровень есть в словаре цветов
        if levelname in LOG_COLORS:
            record.levelname = f"{LOG_COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        # Форматируем сообщение
        message = super().format(record)
        # Восстанавливаем исходное имя уровня
        record.levelname = levelname
        return message


# Форматтер для файла (без цветов)
file_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Форматтер для консоли (с цветами)
console_formatter = ColoredFormatter(
    "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Обработчик для файла с ротацией (максимум 5 файлов по 5MB)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(file_formatter)

# Обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)

# Настройка корневого логгера
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG if settings.dev else logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


# Функция для получения логгера для модуля
def get_logger(name):
    logger = logging.getLogger(name)
    return logger

# Примеры использования:
# from log_setup import get_logger
# logger = get_logger(__name__)
# logger.debug("Отладочное сообщение")
# logger.info("Информационное сообщение")
# logger.warning("Предупреждение")
# logger.error("Ошибка")
# logger.critical("Критическая ошибка")
