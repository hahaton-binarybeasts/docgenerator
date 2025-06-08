from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


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
    status: JobStatus
    type: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class Project(BaseModel):
    id: UUID
    name: str
    repository: str
    directory: str
    access_token: str
    branches: List[str]
    doc_language: str
    doc_type: JobType
    instructions: Optional[str]
    docs_repository: Optional[str]
    docs_url: Optional[str]
    jobs: Optional[List[Job]] = []
    created_at: datetime
    updated_at: datetime