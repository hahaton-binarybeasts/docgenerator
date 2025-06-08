__all__ = ["settings"]

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, \
    PyprojectTomlConfigSettingsSource

CURRENT_DIR = Path(__file__).parent


class AppData(BaseSettings):
    """
    Основная информация о приложении

    :var name: Название приложения
    :var version: Версия приложения
    :var description: Описание приложения
    :var authors: Авторы приложения
    """
    name: str
    version: str
    description: str
    authors: list[dict[str, str]]

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls, CURRENT_DIR.parent / "pyproject.toml"),)

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=('project',),
        extra="ignore",
    )


class Remote(BaseSettings):
    base_url: str = "https://duke.andreis-vibes.ru"
    timeout: float = 10  # seconds

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR.parent / ".env",
        env_file_encoding="utf-8",
        env_prefix="REMOTE__",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


class AI(BaseSettings):
    key: str
    domain: str
    base_url: str = "https://gpt.orionsoft.ru/api/External"
    timeout: float = 3
    operating_system_code: int = 12

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR.parent / ".env",
        env_file_encoding="utf-8",
        env_prefix="AI__",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    project: AppData = AppData()  # type: ignore[call-arg]
    dev: bool = False
    project_root: Path = CURRENT_DIR
    remote: Remote = Remote()
    ai: AI = AI()

    model_config = SettingsConfigDict(
        env_file=CURRENT_DIR.parent / ".env",
        env_file_encoding="utf-8",
        env_prefix="CONFIG__",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


# Использование
settings = Settings()  # type: ignore

if __name__ == "__main__":
    from pprint import pprint

    pprint(settings.model_dump())
