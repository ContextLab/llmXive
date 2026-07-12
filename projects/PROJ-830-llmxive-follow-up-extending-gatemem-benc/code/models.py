"""
Base data models for the GateMem Gatekeeper extension.

Defines Pydantic models for Query, MemoryChunk, DeletionLog, and EvaluationResult.
These models are used throughout the pipeline for type safety and data validation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class Query(BaseModel):
    """Represents an incoming user query to the system."""
    id: str = Field(..., description="Unique identifier for the query")
    text: str = Field(..., description="The raw query text")
    user_role: str = Field(..., description="The role of the user making the query")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the query was made")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional query metadata")

    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query text cannot be empty')
        return v.strip()


class MemoryChunk(BaseModel):
    """Represents a chunk of memory retrieved or stored in the system."""
    id: str = Field(..., description="Unique identifier for the memory chunk")
    content: str = Field(..., description="The text content of the memory chunk")
    source: str = Field(..., description="Source of the memory chunk (e.g., dataset name)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the chunk")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the chunk was created")
    is_deleted: bool = Field(default=False, description="Whether this chunk is marked for deletion")

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Memory chunk content cannot be empty')
        return v.strip()


class DeletionLog(BaseModel):
    """
    Represents a deletion log entry.
    
    Note: This model aligns with the DeletionLog dataclass in gatekeeper/rules.py
    but provides a Pydantic version for API serialization and validation.
    """
    target_id: str = Field(..., description="ID of the target to be deleted")
    reason: Optional[str] = Field(None, description="Reason for deletion")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the deletion was requested")
    status: str = Field(default="pending", description="Status of deletion: pending, completed, failed")
    requester_role: Optional[str] = Field(None, description="Role of the user requesting deletion")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = {"pending", "completed", "failed"}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class EvaluationResult(BaseModel):
    """
    Represents the result of evaluating a query against the gatekeeper and memory system.
    
    Contains the decision made, scores, and any relevant metrics.
    """
    query_id: str = Field(..., description="ID of the query being evaluated")
    memory_chunk_id: Optional[str] = Field(None, description="ID of the memory chunk involved (if any)")
    decision: str = Field(..., description="Final decision: 'allow', 'block', 'partial'")
    access_control_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score for access control (0-1)")
    forgetting_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score for forgetting (0-1)")
    utility_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score for utility (0-1)")
    is_leak: bool = Field(default=False, description="Whether this interaction constitutes a data leak")
    reason: Optional[str] = Field(None, description="Explanation for the decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the evaluation occurred")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional evaluation metadata")

    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        valid_decisions = {"allow", "block", "partial"}
        if v not in valid_decisions:
            raise ValueError(f'Decision must be one of {valid_decisions}')
        return v