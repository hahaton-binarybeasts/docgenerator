import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set

from ai_docsgen.ai.api import AiAPI
from ai_docsgen.config import Settings
from ai_docsgen.git.scm import Scm
from ai_docsgen.log_setup import get_logger
from ai_docsgen.schemas import Project, TreeItem

log = get_logger(__name__)


class PipelineWorker:
    """Класс для генерации документации на основе репозитория"""

    def __init__(self, ai_instance: AiAPI = None):
        """
        Инициализация пайплайна

        Args:
            ai_instance: Экземпляр AI API (если None, будет создан новый)
        """
        self.ai_instance = ai_instance or AiAPI()
        self.prompt_path = Path(__file__).parent / "prompts" / "struct.txt"
        log.info("PipelineWorker инициализирован")
        log.debug(f"Путь к промпту: {self.prompt_path}")

    def _read_prompt(self) -> str:
        """Чтение промпта из файла"""
        log.debug(f"Чтение промпта из {self.prompt_path}")
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            log.debug(f"Промпт успешно прочитан, размер: {len(prompt)} символов")
            return prompt
        except Exception as e:
            log.error(f"Ошибка при чтении промпта: {e}")
            raise

    def _get_directory_structure(self, scm_client: Scm, repo_name: str, branch: str,
                               base_path: str = "", processed_dirs: Set[str] = None) -> List[TreeItem]:
        """
        Рекурсивно получает структуру директорий репозитория

        Args:
            scm_client: SCM клиент
            repo_name: Имя репозитория
            branch: Ветка
            base_path: Базовый путь для начала обхода
            processed_dirs: Множество уже обработанных директорий (для избежания циклов)

        Returns:
            List[TreeItem]: Список всех элементов дерева
        """
        if processed_dirs is None:
            processed_dirs = set()

        if base_path in processed_dirs:
            return []

        processed_dirs.add(base_path)
        log.info(f"Получение структуры для директории: {base_path if base_path else 'Корень'}")

        try:
            # Получаем содержимое текущей директории
            items = scm_client.get_repository_structure(
                repo_name=repo_name,
                branch=branch,
                path=base_path
            )

            result = items.copy()

            # Рекурсивно обходим поддиректории
            for item in items:
                if item.type == "tree":  # это директория
                    subdir_items = self._get_directory_structure(
                        scm_client=scm_client,
                        repo_name=repo_name,
                        branch=branch,
                        base_path=item.path,
                        processed_dirs=processed_dirs
                    )
                    result.extend(subdir_items)

            return result

        except Exception as e:
            log.error(f"Ошибка при получении структуры директории {base_path}: {e}")
            return []

    def _get_module_files(self, tree_items: List[TreeItem]) -> Dict[str, List[str]]:
        """
        Группирует файлы по директориям (модулям)

        Args:
            tree_items: Список элементов дерева файлов

        Returns:
            Dict[str, List[str]]: Словарь {директория: [файлы]}
        """
        log.info(f"Группировка {len(tree_items)} файлов по директориям")
        modules = {}

        # Сначала добавляем корневую директорию
        modules[""] = []

        for item in tree_items:
            if item.type == "blob" and item.path.endswith(('.py', '.js', '.ts', '.go', '.rs', '.cs')):
                # Определяем директорию файла
                directory = os.path.dirname(item.path)

                if directory not in modules:
                    modules[directory] = []
                    log.debug(f"Создана новая директория: {directory}")

                modules[directory].append(item.path)
                log.debug(f"Файл {item.path} добавлен в директорию {directory}")

        # Удалим пустые директории
        modules = {dir_path: files for dir_path, files in modules.items() if files}

        log.info(f"Сгруппировано {sum(len(files) for files in modules.values())} файлов в {len(modules)} директорий")
        return modules

    def _generate_docs_for_module(self, module_name: str, file_paths: List[str],
                                  scm_client: Scm, project: Project) -> str:
        """
        Генерирует документацию для модуля

        Args:
            module_name: Имя модуля (путь к директории)
            file_paths: Пути к файлам модуля
            scm_client: SCM клиент для доступа к репозиторию
            project: Информация о проекте

        Returns:
            str: Markdown документация
        """
        log.info(f"Генерация документации для директории {module_name} ({len(file_paths)} файлов)")

        # Загружаем содержимое файлов
        files_content = []
        for file_path in file_paths:
            try:
                log.debug(f"Загрузка содержимого файла {file_path}")
                content = scm_client.get_file_content(
                    repo_name=project.repository,
                    file_path=file_path,
                    owner=None,  # Используем текущего пользователя
                    branch=project.branches[0] if project.branches else "main"
                )
                files_content.append({
                    "path": file_path,
                    "content": content.content
                })
                log.debug(f"Файл {file_path} успешно загружен, размер: {len(content.content)} символов")
            except Exception as e:
                log.error(f"Ошибка при загрузке файла {file_path}: {e}")

        # Создаем запрос для AI
        log.debug("Чтение промпта для генерации документации")
        prompt = self._read_prompt()

        # Формируем название модуля для AI
        display_module_name = module_name if module_name else "Корневая директория"

        # Формируем запрос с содержимым файлов
        request = f"{prompt}\n\n## ФАЙЛЫ ДИРЕКТОРИИ {display_module_name}:\n\n"

        for file in files_content:
            request += f"### Файл: {file['path']}\n```\n{file['content']}\n```\n\n"

        # Добавляем дополнительные инструкции из проекта, если есть
        if project.instructions:
            log.debug("Добавлены дополнительные инструкции из проекта")
            request += f"\n## ДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ:\n{project.instructions}\n"

        # Отправляем запрос в AI
        log.info(f"Отправка запроса в AI для директории {display_module_name}, размер запроса: {len(request)} символов")
        dialog = self.ai_instance.new_dialog()
        try:
            log.debug("Ожидание ответа от AI...")
            response = dialog.ask_ai(request)
            log.info(f"Получен ответ от AI для директории {display_module_name}, размер: {len(response)} символов")
            return response
        except Exception as e:
            log.error(f"Ошибка при генерации документации для директории {display_module_name}: {e}")
            return f"# Ошибка при генерации документации\n\nДиректория: {display_module_name}\nОшибка: {str(e)}"

    def _build_directory_tree(self, modules: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Строит иерархическое дерево директорий

        Args:
            modules: Словарь {директория: [файлы]}

        Returns:
            Dict[str, List[str]]: Иерархическое дерево директорий
        """
        # Сортируем директории для корректного порядка обхода
        sorted_dirs = sorted(modules.keys())

        # Создаем словарь для хранения дерева
        tree = {}

        # Для каждой директории добавляем все родительские пути
        for dir_path in sorted_dirs:
            parts = dir_path.split('/')
            current_path = ""

            # Добавляем каждый уровень вложенности в дерево
            for i, part in enumerate(parts):
                if not part and i == 0:  # Пропускаем пустой первый элемент
                    continue

                parent_path = current_path
                if parent_path and part:
                    current_path = f"{parent_path}/{part}"
                else:
                    current_path = part if part else ""

                # Добавляем директорию в дерево, если её еще нет
                if current_path not in tree and current_path:
                    tree[current_path] = []

        # Добавляем корневую директорию, если её нет
        if "" not in tree:
            tree[""] = []

        # Добавляем файлы в соответствующие директории
        for dir_path, files in modules.items():
            if dir_path in tree:
                tree[dir_path].extend(files)

        return tree

    def process(self, project: Project) -> str:
        """
        Основной метод обработки проекта и генерации документации

        Args:
            project: Информация о проекте

        Returns:
            str: Путь к директории с сгенерированной документацией
        """
        log.info(f"Начало обработки проекта {project.name} (репозиторий: {project.repository})")

        # Создаем SCM клиент
        log.debug("Инициализация SCM клиента")
        scm_client = Scm(auth_token=project.access_token)

        # Создаем временную директорию для документации
        temp_dir = Path(tempfile.mkdtemp(prefix="docgen_"))
        log.info(f"Создана временная директория для документации: {temp_dir}")

        try:
            # Получаем структуру репозитория рекурсивно
            log.info(f"Получение структуры репозитория {project.repository} (рекурсивно)")
            branch = project.branches[0] if project.branches else "main"
            base_path = project.directory or ""

            tree_items = self._get_directory_structure(
                scm_client=scm_client,
                repo_name=project.repository,
                branch=branch,
                base_path=base_path
            )
            log.info(f"Получено {len(tree_items)} элементов структуры репозитория")
            log.debug(f"Структура репозитория:\n{tree_items}")

            # Группируем файлы по директориям
            log.debug("Группировка файлов по директориям")
            modules = self._get_module_files(tree_items)

            # Строим полное дерево директорий
            directory_tree = self._build_directory_tree(modules)
            log.info(f"Построено дерево директорий с {len(directory_tree)} узлами")

            # Создаем README.md в корне с общей информацией
            readme_path = temp_dir / "README.md"
            log.info(f"Создание основного README в {readme_path}")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# Документация проекта {project.name}\n\n")
                f.write("## Структура проекта\n\n")

                # Создаем структуру проекта в README
                for module_path in sorted(directory_tree.keys()):
                    display_path = module_path if module_path else "/"
                    path_depth = len(display_path.split('/')) - 1 if module_path else 0
                    indent = "  " * path_depth
                    doc_path = module_path.replace('/', '/') if module_path else "."
                    f.write(f"{indent}- [{display_path}]({doc_path}/description.md)\n")

            log.debug(f"README успешно создан с информацией о {len(directory_tree)} директориях")

            # Генерируем документацию для каждой директории
            for module_path, file_paths in modules.items():
                try:
                    log.info(f"Обработка директории {module_path if module_path else 'Корень'}")

                    # Генерируем документацию для директории
                    doc_content = self._generate_docs_for_module(
                        module_name=module_path,
                        file_paths=file_paths,
                        scm_client=scm_client,
                        project=project
                    )

                    # Определяем путь для сохранения документации
                    # Если это корневая директория, сохраняем в корне temp_dir
                    if module_path:
                        # Создаем структуру директорий
                        module_dir = temp_dir / module_path
                        module_dir.mkdir(parents=True, exist_ok=True)
                        doc_file_path = module_dir / "description.md"
                    else:
                        doc_file_path = temp_dir / "description.md"

                    log.info(f"Сохранение документации для директории {module_path if module_path else 'Корень'} в {doc_file_path}")
                    with open(doc_file_path, "w", encoding="utf-8") as f:
                        f.write(doc_content)
                    log.debug(f"Документация для директории {module_path if module_path else 'Корень'} успешно сохранена")

                except Exception as e:
                    log.error(f"Ошибка при обработке директории {module_path}: {e}")

            log.info(f"Обработка проекта {project.name} завершена успешно")
            return str(temp_dir)

        except Exception as e:
            log.error(f"Ошибка при обработке проекта {project.name}: {e}")
            return str(e)


if __name__ == "__main__":
    worker = PipelineWorker()

    project = Project(
        id=uuid.uuid4(),
        name="test",
        repository="https://github.com/MigAru/poseidon",
        directory="",
        access_token=Settings().gh_token,
        branches=['main'],
        doc_language="russian",
        doc_type="full",
        instructions="",
        docs_repository="",
        docs_url="",
        jobs=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    worker.process(project=project)
