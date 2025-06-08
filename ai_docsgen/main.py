from datetime import datetime, time
import logging
from time import sleep
from typing import List


from ai_docsgen.config import settings
from ai_docsgen.log_setup import get_logger
from ai_docsgen.client import RestApiClient
from ai_docsgen.schemas import Job, Project, JobStatus

logger = get_logger(__name__)



def fetch_updates(client: RestApiClient):

   # Получаем актуальные проекты
   return client.get_projects()

        


def main():
    logger.info("Запуск приложения")
    do_run = True
    client = RestApiClient(settings.remote.base_url)
    while do_run:
        try:
            logger.info("Проверка наличия задач")
            projects = fetch_updates(client)
            for p in projects:
                project = client.get_project(p.id)
                for j in project.jobs:
                    if j.status == JobStatus.PENDING:
                        client.update_job_status(id=id, status=JobStatus.RUNNING, completed_at=datetime.now())
                        # start_generation(j) # not implemented
            sleep(settings.remote.timeout)
        except Exception as e:
            logging.critical(f"Произошла ошибка: {e}")
    logger.info("Завершение приложения")

if __name__ == "__main__":
    main()