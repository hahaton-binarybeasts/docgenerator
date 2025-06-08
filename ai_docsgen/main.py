import logging
from time import sleep

import requests

from ai_docsgen.config import settings
from ai_docsgen.log_setup import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Запуск приложения")
    do_run = True
    while do_run:
        try:
            logger.info("Проверка наличия задач")
            response = requests.get(settings.remote.base_url + "/jobs")
            print(response.json())

            sleep(settings.remote.timeout)
        except Exception as e:
            logging.critical(f"Произошла ошибка: {e}")
    logger.info("Завершение приложения")

if __name__ == "__main__":
    main()