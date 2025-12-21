from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Generic, TypeVar, Literal, Union
from uuid import UUID
from datetime import datetime

T = TypeVar("T")

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    username: str
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# GitHub
class RepoOwner(BaseModel):
    login: str
    avatar_url: str
    model_config = ConfigDict(from_attributes=True)

class RepoResponse(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    stars: int = Field(alias="stargazers_count")
    forks: int = Field(alias="forks_count")
    updated_at: datetime
    language: Optional[str] = None
    owner: RepoOwner
    model_config = ConfigDict(from_attributes=True)

class ContributorResponse(BaseModel):
    username: str
    avatar_url: str
    commits: int
    additions: int
    deletions: int
    percentage: float
    model_config = ConfigDict(from_attributes=True)

class CommitAuthor(BaseModel):
    username: str
    avatar_url: str
    model_config = ConfigDict(from_attributes=True)

class CommitResponse(BaseModel):
    sha: str
    message: str
    author: CommitAuthor
    date: datetime
    additions: Optional[int] = None
    deletions: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class FileTreeItem(BaseModel):
    path: str
    type: Literal["blob", "tree"]  # blob = file, tree = directory
    sha: str
    size: Optional[int] = None
    url: str
    model_config = ConfigDict(from_attributes=True)

class FileTreeResponse(BaseModel):
    sha: str
    url: str
    tree: List[FileTreeItem]
    truncated: bool
    model_config = ConfigDict(from_attributes=True)

# Judgment
class JudgmentCreate(BaseModel):
    repo_owner: str
    repo_name: str
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    file_path: Optional[str] = None
    period_days: int = Field(default=7, ge=1, le=90)

class SuspectResponse(BaseModel):
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    responsibility: int
    reason: Optional[str] = None
    commit_count: Optional[int] = None
    last_commit_msg: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class BlameMessages(BaseModel):
    mild: List[str]
    medium: List[str]
    spicy: List[str]

class BlameResponse(BaseModel):
    id: UUID
    target_username: str
    target_avatar: Optional[str] = None
    responsibility: int
    reason: Optional[str] = None
    messages: BlameMessages
    image_url: Optional[str] = None
    created_at: datetime

class JudgmentResponse(BaseModel):
    id: UUID
    case_number: str
    repo_owner: str
    repo_name: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    period_days: int
    status: str
    created_at: datetime
    suspects: List[SuspectResponse] = []
    blame: Optional[BlameResponse] = None
    model_config = ConfigDict(from_attributes=True)

class JudgmentListResponse(BaseModel):
    id: UUID
    case_number: str
    repo_name: str
    title: str
    status: str
    has_blame: bool = False # Computed field? Or needs to be mapped
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Blame
class BlameCreate(BaseModel):
    pass  # No fields needed - generates all intensities

# Common
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    model_config = ConfigDict(from_attributes=True)
