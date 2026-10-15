"""
Pydantic data‑model definitions for the core entities used throughout the
project.  The test‑suite expects these models to raise ``pydantic.ValidationError``
on invalid input, therefore we implement them as ``BaseModel`` subclasses.
Updated for Pydantic v2.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

# ----------------------------------------------------------------------
# Enum definitions
# ----------------------------------------------------------------------
class NodeStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ExecutionStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# ----------------------------------------------------------------------
# Core models
# ----------------------------------------------------------------------
class PhysicalNode(BaseModel):
    node_id: str = Field(..., description="Unique identifier for the node")
    hostname: str = Field(..., description="IP address or resolvable host name")
    username: str = Field(..., description="User used for SSH connections")
    hardware_spec: Dict[str, Any] = Field(..., description="Arbitrary hardware description")
    port: int = Field(22, ge=1, le=65535, description="SSH port")
    status: NodeStatus = Field(NodeStatus.IDLE, description="Current node status")
    latency_ms: float = Field(0.0, ge=0.0, description="Measured network latency")
    bandwidth_mbps: float = Field(0.0, ge=0.0, description="Measured bandwidth")

    @field_validator('hardware_spec')
    @classmethod
    def hardware_spec_must_be_dict(cls, v):
        if not isinstance(v, dict):
            raise ValueError('hardware_spec must be a dict')
        return v

class TaskChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    task_type: str = Field(..., description="Type of task, e.g. 'monte_carlo'")
    payload: Dict[str, Any] = Field(..., description="Parameters for the task")
    expected_duration_sec: float = Field(..., gt=0, description="Estimated runtime in seconds")

    @field_validator('payload')
    @classmethod
    def payload_must_be_dict(cls, v):
        if not isinstance(v, dict):
            raise ValueError('payload must be a dict')
        return v

class ExecutionRun(BaseModel):
    run_id: str = Field(..., description="Unique identifier for the execution run")
    node_ids: List[str] = Field(..., min_length=1, description="List of participating node IDs")
    task_chunks: List[TaskChunk] = Field(default_factory=list, description="Chunks assigned in this run")
    config_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Copy of the configuration used")
    status: ExecutionStatus = Field(ExecutionStatus.PLANNED, description="Overall run status")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    coordination_overhead_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Ratio of coordination overhead to total execution time"
    )

    @model_validator(mode='after')
    def check_node_ids_unique(self) -> 'ExecutionRun':
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError('duplicate node IDs are not allowed')
        return self

    @model_validator(mode='after')
    def check_chunk_ids_unique(self) -> 'ExecutionRun':
        ids = [c.chunk_id for c in self.task_chunks]
        if len(set(ids)) != len(ids):
            raise ValueError('duplicate chunk IDs are not allowed')
        return self

    @model_validator(mode='after')
    def check_time_consistency(self) -> 'ExecutionRun':
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValueError('end_time cannot be before start_time')
        if self.status == ExecutionStatus.COMPLETED:
            if not self.end_time:
                raise ValueError('completed runs must have an end_time')
        return self

    @property
    def total_wall_clock_time_sec(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
