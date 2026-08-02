"""
Base data models for the Mesh Network Supercomputer Orchestrator.

Defines Pydantic models for PhysicalNode, TaskChunk, and ExecutionRun
with strict validation as required by the project specification.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class NodeStatus(str, Enum):
    """Status of a physical node in the mesh."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Status of a task chunk during execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ExecutionStatus(str, Enum):
    """Status of a full execution run."""
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class PhysicalNode(BaseModel):
    """
    Represents a physical node in the mesh network.
    
    Attributes:
        node_id: Unique identifier for the node.
        hostname: SSH hostname or IP address.
        port: SSH port (default 22).
        username: SSH username.
        hardware_spec: JSON-serializable dict of hardware specs (CPU, RAM, etc.).
        status: Current operational status.
        last_heartbeat: Timestamp of last successful heartbeat.
        latency_ms: Measured network latency to this node (ms).
        bandwidth_mbps: Measured bandwidth capacity (Mbps).
        snr_db: Measured Signal-to-Noise Ratio (dB).
    """
    node_id: str = Field(..., description="Unique identifier for the node")
    hostname: str = Field(..., description="SSH hostname or IP address")
    port: int = Field(22, ge=1, le=65535, description="SSH port")
    username: str = Field(..., description="SSH username")
    hardware_spec: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hardware specifications (CPU, RAM, architecture)"
    )
    status: NodeStatus = Field(NodeStatus.IDLE, description="Current node status")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    latency_ms: Optional[float] = Field(None, ge=0, description="Network latency in ms")
    bandwidth_mbps: Optional[float] = Field(None, ge=0, description="Bandwidth in Mbps")
    snr_db: Optional[float] = Field(None, description="Signal-to-Noise Ratio in dB")

    @field_validator('hardware_spec')
    @classmethod
    def validate_hardware_spec(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError('hardware_spec must be a dictionary')
        return v

    @model_validator(mode='after')
    def check_required_hardware_fields(self) -> PhysicalNode:
        # Ensure at least some basic hardware info is present if spec is provided
        if self.hardware_spec and 'cpu_arch' not in self.hardware_spec:
            # Allow missing for now, but could enforce if spec requires it
            pass
        return self


class TaskChunk(BaseModel):
    """
    Represents a chunk of work to be executed on a node.
    
    Attributes:
        chunk_id: Unique identifier for the task chunk.
        task_type: Type of task (e.g., 'monte_carlo', 'matrix_mult').
        payload: Task-specific parameters/data.
        expected_duration_sec: Estimated execution time in seconds.
        status: Current execution status.
        assigned_node_id: ID of the node assigned to this chunk.
        start_time: When execution started.
        end_time: When execution completed/failed.
        result_data: Path to result data or serialized result.
        error_message: Error details if failed.
    """
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    task_type: str = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    expected_duration_sec: float = Field(1.0, gt=0, description="Expected duration in seconds")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current status")
    assigned_node_id: Optional[str] = Field(None, description="Assigned node ID")
    start_time: Optional[datetime] = Field(None, description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    result_data: Optional[str] = Field(None, description="Path to result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError('payload must be a dictionary')
        return v

    @model_validator(mode='after')
    def validate_timing(self) -> TaskChunk:
        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                raise ValueError('end_time cannot be before start_time')
        if self.status == TaskStatus.COMPLETED and not self.result_data:
            # Allow result_data to be optional for now, but warn if missing
            pass
        return self


class ExecutionRun(BaseModel):
    """
    Represents a single execution run of the mesh supercomputer.
    
    Attributes:
        run_id: Unique identifier for the execution run.
        created_at: Timestamp when the run was created.
        status: Current status of the run.
        node_ids: List of node IDs participating in this run.
        task_chunks: List of task chunks assigned to this run.
        start_time: When the run started.
        end_time: When the run completed/aborted.
        total_wall_clock_time_sec: Total elapsed time in seconds.
        coordination_overhead_ratio: Ratio of handshake time to total time.
        network_saturation_detected: Whether network saturation was detected.
        error_code: Error code if the run failed.
        config_snapshot: Snapshot of configuration used for this run.
    """
    run_id: str = Field(..., description="Unique identifier for the run")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    status: ExecutionStatus = Field(ExecutionStatus.PLANNED, description="Run status")
    node_ids: List[str] = Field(default_factory=list, description="Participating node IDs")
    task_chunks: List[TaskChunk] = Field(default_factory=list, description="Task chunks in this run")
    start_time: Optional[datetime] = Field(None, description="Run start timestamp")
    end_time: Optional[datetime] = Field(None, description="Run end timestamp")
    total_wall_clock_time_sec: Optional[float] = Field(None, ge=0, description="Total wall clock time in seconds")
    coordination_overhead_ratio: Optional[float] = Field(None, ge=0, le=1.0, description="Coordination overhead ratio")
    network_saturation_detected: bool = Field(False, description="Whether network saturation was detected")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    config_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Configuration snapshot")

    @field_validator('node_ids')
    @classmethod
    def validate_node_ids(cls, v: List[str]) -> List[str]:
        if not isinstance(v, list):
            raise ValueError('node_ids must be a list')
        if len(v) != len(set(v)):
            raise ValueError('node_ids must be unique')
        return v

    @field_validator('task_chunks')
    @classmethod
    def validate_task_chunks(cls, v: List[TaskChunk]) -> List[TaskChunk]:
        if not isinstance(v, list):
            raise ValueError('task_chunks must be a list')
        chunk_ids = [chunk.chunk_id for chunk in v]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError('task_chunks must have unique chunk_ids')
        return v

    @model_validator(mode='after')
    def validate_run_timing(self) -> ExecutionRun:
        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                raise ValueError('end_time cannot be before start_time')
            if self.total_wall_clock_time_sec is None:
                delta = self.end_time - self.start_time
                self.total_wall_clock_time_sec = delta.total_seconds()
        return self

    @model_validator(mode='after')
    def validate_status_consistency(self) -> ExecutionRun:
        if self.status == ExecutionStatus.COMPLETED:
            if not self.end_time:
                raise ValueError('completed run must have end_time')
            if self.error_code:
                raise ValueError('completed run should not have error_code')
        elif self.status == ExecutionStatus.FAILED or self.status == ExecutionStatus.ABORTED:
            if not self.error_code:
                # Allow missing error_code for aborted/failed but warn
                pass
        return self
