import base64
import os
import subprocess
from pathlib import Path
from typing import Optional, List

from github import Github, Auth
from pydantic import BaseModel, PrivateAttr

from ai_docsgen.log_setup import get_logger
from ai_docsgen.schemas import RepositoryInfo, TreeItem, FileContent

log = get_logger(__name__)


class Scm(BaseModel):
    """Класс для работы с GitHub API"""

    # Приватные атрибуты для PyGithub клиента
    _client: Github = PrivateAttr()
    _auth_token: Optional[str] = PrivateAttr(default=None)

    def __init__(self, auth_token: Optional[str] = None, **data):
        """
        Инициализация SCM клиента

        Args:
            auth_token: GitHub Personal Access Token. Если не указан, доступ только к публичным репозиториям.
        """
        super().__init__(**data)
        self._auth_token = auth_token
        
        if auth_token:
            auth = Auth.Token(auth_token)
            self._client = Github(auth=auth)
        else:
            # Инициализация без аутентификации (для публичных репозиториев)
            self._client = Github()
            log.info("Инициализация SCM клиента без аутентификации. Доступны только публичные репозитории с ограничением запросов.")

    def get_repository_info(self, repo_name: str, owner: Optional[str] = None) -> RepositoryInfo:
        """
        Получение информации о репозитории

        Args:
            repo_name: Имя репозитория в формате "owner/repo" или полный URL
            owner: Владелец репозитория (игнорируется, оставлен для обратной совместимости)

        Returns:
            RepositoryInfo: Информация о репозитории
        """
        try:
            # Нормализация repo_name
            normalized_repo_name = self._normalize_repo_name(repo_name)

            repo = self._client.get_repo(normalized_repo_name)

            return RepositoryInfo(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description,
                private=repo.private,
                html_url=repo.html_url,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                default_branch=repo.default_branch,
                language=repo.language,
                size=repo.size,
                stargazers_count=repo.stargazers_count,
                forks_count=repo.forks_count,
                open_issues_count=repo.open_issues_count,
                created_at=repo.created_at.isoformat(),
                updated_at=repo.updated_at.isoformat(),
                pushed_at=repo.pushed_at.isoformat() if repo.pushed_at else None
            )
        except Exception as e:
            raise Exception(f"Ошибка получения информации о репозитории: {str(e)}")

    def _normalize_repo_name(self, repo_name: str) -> str:
        """
        Нормализует имя репозитория в формат "owner/repo"

        Args:
            repo_name: Имя репозитория в любом формате (URL, owner/repo)

        Returns:
            str: Нормализованное имя репозитория в формате "owner/repo"
        """
        # Удаляем префикс URL если он есть
        normalized = repo_name.replace("https://github.com/", "")
        # Удаляем суффикс .git если он есть
        normalized = normalized.replace(".git", "")
        return normalized

    def get_repository_structure(self, repo_name: str, owner: Optional[str] = None,
                                 branch: str = "main", path: str = "") -> List[TreeItem]:
        """
        Получение структуры проекта (дерева файлов)

        Args:
            repo_name: Имя репозитория в формате "owner/repo" или полный URL
            owner: Владелец репозитория (игнорируется, оставлен для обратной совместимости)
            branch: Ветка (по умолчанию main)
            path: Путь в репозитории (для получения поддиректории)

        Returns:
            List[TreeItem]: Список элементов дерева
        """
        log.info(f"Получение структуры репозитория {repo_name} (ветка: {branch}, путь: {path})")
        try:
            normalized_repo_name = self._normalize_repo_name(repo_name)
            repo = self._client.get_repo(normalized_repo_name)

            contents = repo.get_contents(path, ref=branch)

            # Если contents не является списком, делаем его списком
            if not isinstance(contents, list):
                contents = [contents]

            tree_items = []
            for content in contents:
                tree_items.append(TreeItem(
                    path=content.path,
                    mode="040000" if content.type == "dir" else "100644",
                    type="tree" if content.type == "dir" else "blob",
                    size=content.size if content.type == "file" else None,
                    sha=content.sha
                ))

            return tree_items

        except Exception as e:
            raise Exception(f"Ошибка получения структуры репозитория: {str(e)}")

    def get_file_content(self, repo_name: str, file_path: str,
                         owner: Optional[str] = None, branch: str = "main") -> FileContent:
        """
        Получение содержимого файла

        Args:
            repo_name: Имя репозитория в формате "owner/repo" или полный URL
            file_path: Путь к файлу в репозитории
            owner: Владелец репозитория (игнорируется, оставлен для обратной совместимости)
            branch: Ветка

        Returns:
            FileContent: Содержимое файла
        """
        try:
            normalized_repo_name = self._normalize_repo_name(repo_name)
            repo = self._client.get_repo(normalized_repo_name)

            file = repo.get_contents(file_path, ref=branch)

            # Декодирование содержимого
            if file.encoding == "base64":
                content = base64.b64decode(file.content).decode('utf-8')
            else:
                content = file.content

            return FileContent(
                name=file.name,
                path=file.path,
                content=content,
                encoding=file.encoding,
                size=file.size,
                sha=file.sha
            )

        except Exception as e:
            raise Exception(f"Ошибка получения содержимого файла: {str(e)}")

    def create_repository(self, repo_name: str, description: str = "",
                          private: bool = False, auto_init: bool = True) -> RepositoryInfo:
        """
        Создание удалённого репозитория

        Args:
            repo_name: Имя репозитория
            description: Описание репозитория
            private: Приватный ли репозиторий
            auto_init: Автоматически создать README

        Returns:
            RepositoryInfo: Информация о созданном репозитории
        """
        if not self._auth_token:
            raise Exception("Для создания репозитория требуется аутентификация. Укажите auth_token при инициализации Scm.")
            
        try:
            user = self._client.get_user()
            repo = user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=auto_init
            )

            return RepositoryInfo(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description,
                private=repo.private,
                html_url=repo.html_url,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                default_branch=repo.default_branch,
                language=repo.language,
                size=repo.size,
                stargazers_count=repo.stargazers_count,
                forks_count=repo.forks_count,
                open_issues_count=repo.open_issues_count,
                created_at=repo.created_at.isoformat(),
                updated_at=repo.updated_at.isoformat(),
                pushed_at=repo.pushed_at.isoformat() if repo.pushed_at else None
            )

        except Exception as e:
            raise Exception(f"Ошибка создания репозитория: {str(e)}")

    def init_and_push_local_repo(self, local_path: str, repo_name: str,
                                 commit_message: str = "Initial commit",
                                 branch: str = "main") -> bool:
        """
        Инициализация локального репозитория и пуш в GitHub

        Args:
            local_path: Путь к локальной папке
            repo_name: Имя репозитория на GitHub
            commit_message: Сообщение коммита
            branch: Основная ветка

        Returns:
            bool: Успешность операции
        """
        if not self._auth_token:
            raise Exception("Для операций с локальным репозиторием требуется аутентификация. Укажите auth_token при инициализации Scm.")
            
        try:
            local_path = Path(local_path).resolve()

            # Проверяем существование папки
            if not local_path.exists():
                raise Exception(f"Папка {local_path} не существует")

            # Получаем информацию о пользователе для формирования URL
            user = self._client.get_user()
            normalized_repo_name = self._normalize_repo_name(repo_name)

            # Если repo_name уже содержит имя владельца, используем его
            if "/" in normalized_repo_name:
                repo_url = f"https://github.com/{normalized_repo_name}.git"
            else:
                repo_url = f"https://github.com/{user.login}/{normalized_repo_name}.git"

            # Переходим в директорию
            os.chdir(local_path)

            # Проверяем, не является ли папка уже git репозиторием
            if not (local_path / ".git").exists():
                # Инициализируем git репозиторий
                subprocess.run(["git", "init"], check=True, capture_output=True)
                subprocess.run(["git", "branch", "-M", branch], check=True, capture_output=True)

            # Добавляем все файлы
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Проверяем, есть ли изменения для коммита
            result = subprocess.run(["git", "status", "--porcelain"],
                                    capture_output=True, text=True)

            if result.stdout.strip():  # Есть изменения
                # Создаем коммит
                subprocess.run(["git", "commit", "-m", commit_message],
                               check=True, capture_output=True)

            # Добавляем remote origin если его нет
            remotes_result = subprocess.run(["git", "remote"],
                                            capture_output=True, text=True)

            if "origin" not in remotes_result.stdout:
                subprocess.run(["git", "remote", "add", "origin", repo_url],
                               check=True, capture_output=True)
            else:
                # Обновляем URL remote origin
                subprocess.run(["git", "remote", "set-url", "origin", repo_url],
                               check=True, capture_output=True)

            # Пушим в репозиторий
            subprocess.run(["git", "push", "-u", "origin", branch],
                           check=True, capture_output=True)

            return True

        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка выполнения git команды: {e}")
        except Exception as e:
            raise Exception(f"Ошибка инициализации и пуша репозитория: {str(e)}")

    def create_and_push_repository(self, local_path: str, repo_name: str,
                                   description: str = "", private: bool = False,
                                   commit_message: str = "Initial commit") -> RepositoryInfo:
        """
        Создание репозитория на GitHub и пуш локальной папки
        
        Args:
            local_path: Путь к локальной папке
            repo_name: Имя репозитория
            description: Описание репозитория
            private: Приватный ли репозиторий
            commit_message: Сообщение коммита
            
        Returns:
            RepositoryInfo: Информация о созданном репозитории
        """
        if not self._auth_token:
            raise Exception("Для создания и пуша репозитория требуется аутентификация. Укажите auth_token при инициализации Scm.")
            
        # Создаем репозиторий на GitHub (без auto_init, чтобы избежать конфликтов)
        repo_info = self.create_repository(
            repo_name=repo_name,
            description=description,
            private=private,
            auto_init=False
        )

        # Инициализируем и пушим локальный репозиторий
        self.init_and_push_local_repo(
            local_path=local_path,
            repo_name=repo_name,
            commit_message=commit_message
        )

        return repo_info
