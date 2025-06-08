__all__ = ["AiApiException", "AiAPI", "DialogAPI"]

import json
import uuid
from time import sleep

import requests

from ai_docsgen.config import settings
from ai_docsgen.log_setup import get_logger

log = get_logger(__name__)


class AiApiException(Exception):
    pass


class AiAPI:
    def __init__(
            self,
            base_url: str = settings.ai.base_url,
            key: str = settings.ai.key,
            domain: str = settings.ai.domain,
            operating_system_code: int = settings.ai.operating_system_code):
        self.base_url = base_url.rstrip("/")
        self.key = key
        self.domain = domain
        self.operating_system_code = operating_system_code

    def new_dialog(self):
        return DialogAPI(self, f"{self.domain}_{uuid.uuid4()}")


class DialogAPI:
    new_request_url = "/PostNewRequest"
    get_messages_url = "/GetNewResponse"
    complete_session_url = "/CompleteSession"

    def __init__(
            self,
            api: AiAPI,
            dialog_id: str,
    ):
        self.api = api
        self.dialog_id = dialog_id

    def _send_message(self, message: str, retry_count: int = 3) -> bool:
        _data = {
            "operatingSystemCode": self.api.operating_system_code,
            "apiKey": self.api.key,
            "userDomainName": self.api.domain,
            "dialogIdentifier": self.dialog_id,
            "aiModelCode": 1,
            "Message": message
        }

        for _ in range(retry_count):
            try:
                response = requests.post(self.api.base_url + self.new_request_url, json=_data)

                if response.status_code != 200:
                    log.warning("Ошибка ответа: %s", response.status_code)
                    raise AiApiException(response.status_code)
                return True
            except Exception as e:
                log.error("Произошла ошибка при запросе: %s", e)
                sleep(settings.ai.timeout)

        log.error("Превышено количество попыток запроса: %s", retry_count)
        raise AiApiException("Превышено количество попыток запроса")

    def _get_message(self, retry_count: int = 3):
        _data = {
            "operatingSystemCode": self.api.operating_system_code,
            "apiKey": self.api.key,
            "dialogIdentifier": self.dialog_id
        }

        for _ in range(retry_count):
            try:
                response = requests.post(self.api.base_url + self.get_messages_url, json=_data)

                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        if response_json.get("status", {}).get("isSuccess"):
                            message = response_json.get("data", {}).get("lastMessage")
                            if message:
                                return message
                            else:
                                log.warning("Ответ пока не готов.")
                                return None
                        else:
                            error_desc = response_json.get("status", {}).get("description")
                            # log.error("Ошибка от сервера: %s", error_desc)
                            raise AiApiException(f"Ошибка от сервера: {error_desc}")
                    except json.JSONDecodeError:
                        # log.error("Ошибка декодирования JSON.")
                        raise AiApiException("Ошибка декодирования JSON.")
                else:
                    # log.warning("Ошибка ответа: %s", response.status_code)
                    raise AiApiException(f"Ошибка получения ответа: {response.status_code}")
            except Exception as e:
                # log.error("Произошла ошибка при запросе: %s", e)
                sleep(settings.ai.timeout)

        # log.error("Превышено количество попыток запроса: %s", retry_count)
        raise AiApiException("Превышено количество попыток запроса")

    def clear_context(self, retry_count: int = 3):
        _data = {
            "operatingSystemCode": self.api.operating_system_code,
            "apiKey": self.api.key,
            "dialogIdentifier": self.dialog_id
        }

        for _ in range(retry_count):
            try:
                response = requests.post(self.api.base_url + self.complete_session_url, json=_data)

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get("isSuccess"):
                            return True
                        else:
                            error_desc = result.get("description", "Неизвестная ошибка")
                            log.error("Ошибка очистки контекста: %s", error_desc)
                            raise AiApiException(f"Ошибка очистки контекста: {error_desc}")
                    except json.JSONDecodeError:
                        log.error("Ошибка декодирования JSON при очистке контекста.")
                        raise AiApiException("Ошибка декодирования JSON при очистке контекста.")
                else:
                    log.warning("Ошибка ответа при очистке контекста: %s", response.status_code)
                    raise AiApiException(f"Ошибка при очистке контекста: {response.status_code}")
            except Exception as e:
                log.error("Произошла ошибка при запросе очистки контекста: %s", e)
                sleep(settings.ai.timeout)

        log.error("Превышено количество попыток запроса очистки контекста: %s", retry_count)
        raise AiApiException("Превышено количество попыток запроса очистки контекста")

    def ask_ai(self, message: str, max_attempts: int = 50) -> str:
        """
        Отправляет сообщение и ожидает ответа от API с повторными попытками.
        
        Args:
            message: Текст сообщения для отправки
            max_attempts: Максимальное количество попыток получения ответа
            
        Returns:
            str: Полученный ответ от API
            
        Raises:
            AiApiException: Если ответ не получен за указанное количество попыток
        """
        # Отправляем сообщение
        if not self._send_message(message):
            raise AiApiException("Не удалось отправить сообщение")
        else:
            log.info("Сообщение отправлено")

        # Ожидаем ответа
        for attempt in range(max_attempts):
            try:
                response = self._get_message()
            except Exception as e:
                response = None
            if response:
                return response

            log.info(f"Ожидание ответа... Попытка {attempt + 1}/{max_attempts}")
            sleep(settings.ai.timeout)

        raise AiApiException(f"Не удалось получить ответ за {max_attempts} попыток")


if __name__ == "__main__":
    api = AiAPI()
    dialog = api.new_dialog()
    print(dialog.ask_ai("Привет! Как дела?"))
    print(dialog.ask_ai("Страдаю :'("))
    print(dialog.ask_ai("Пытают, гады!"))
