from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime
from uuid import UUID


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