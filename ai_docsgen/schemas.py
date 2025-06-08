from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

<<<<<<< HEAD
class DocType(str, Enum):
    FULL = "full"
    PRIVATE = "private"
    PUBLIC = "public"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    FULL_GENERATION = "full_generation"
    PARTIAL_UPDATE = "partial_update"
    VALIDATION = "validation" # TODO: Выяснить чё это за тип


class Job(BaseModel):
    id: UUID
    project_id: UUID
    branch: str
    commit_id: str
    status: JobStatus
    job_type: JobType
    error_message: Optional[str] = None
    result: Optional[dict] = None
    started_at: datetime
    completed_at: datetime
=======
from pydantic import BaseModel
>>>>>>> parent of fd9376a (add job model)


class Project(BaseModel):
    id: UUID
    name: str
    repository: str
    directory: str
    access_token: str
    branches: List[str]
    doc_language: str
<<<<<<< HEAD
    doc_type: DocType
    instructions: Optional[str]
    docs_repository: Optional[str]
    docs_url: Optional[str]
    jobs: Optional[List[Job]] = []
=======
    doc_type: Literal["full"]
    instructions: str
    docs_repository: str
    docs_url: str
>>>>>>> parent of fd9376a (add job model)
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
