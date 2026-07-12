from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re

class Query(BaseModel):
    """Represents a user query."""
    id: str
    text: str
    domain: Optional[str] = None
    is_personal: bool = False

class MemoryChunk(BaseModel):
    """Represents a memory chunk."""
    id: str
    content: str
    domain: str
    owner: str
    created_at: datetime = Field(default_factory=datetime.now)

class DeletionLog(BaseModel):
    """Represents a deletion log entry."""
    request_id: str
    user_id: str
    target_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "pending"

class EvaluationResult(BaseModel):
    """Represents an evaluation result."""
    query_id: str
    decision: str
    latency_ms: float
    peak_ram_mb: float
    timestamp: datetime = Field(default_factory=datetime.now)

class RoleDefinition(BaseModel):
    """Represents a role definition."""
    role_name: str
    allowed_domains: List[str] = Field(default_factory=list)
    can_access_personal: bool = False

@field_validator("id")
@classmethod
def validate_id(cls, v: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_-]+$", v):
        raise ValueError("ID must contain only alphanumeric characters, underscores, and hyphens")
    return v
