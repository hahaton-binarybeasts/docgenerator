from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class Project(BaseModel):
    id: UUID
    name: str
    repository: str
    directory: str
    access_token: str
    branches: List[str]
    doc_language: str
    doc_type: Literal["full"]
    instructions: str
    docs_repository: str
    docs_url: str
    created_at: datetime
    updated_at: datetime


class RepositoryInfo(BaseModel):
    """Модель для информации о репозитории"""
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    language: Optional[str]
    size: int
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    created_at: str
    updated_at: str
    pushed_at: Optional[str]


class FileContent(BaseModel):
    """Модель для содержимого файла"""
    name: str
    path: str
    content: str
    encoding: str
    size: int
    sha: str


class TreeItem(BaseModel):
    """Модель для элемента дерева файлов"""
    path: str
    mode: str
    type: str  # 'blob' для файлов, 'tree' для директорий
    size: Optional[int] = None
    sha: str
