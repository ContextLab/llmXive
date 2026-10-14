"""
Data model classes for PhysicalNode, TaskChunk, and ExecutionRun.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PhysicalNode:
    ip: str = field(default_factory=str)
    status: str = "active"
    ram_mb: int = 4096

    # Additional optional metadata retained from the original design
    id: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    node_status: NodeStatus = NodeStatus.ONLINE
    available_memory_mb: Optional[int] = None
    cpu_cores: Optional[int] = None
    last_heartbeat: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.ip_address:
            self.ip_address = self.ip
        if not self.available_memory_mb:
            self.available_memory_mb = self.ram_mb
        if not self.hostname:
            self.hostname = self.ip

@dataclass
class TaskChunk:
    id: str = field(default_factory=str)
    size_mb: float = 0.0
    iterations: int = 0
    data: Any = None

    # Optional fields from the original implementation
    payload: Any = None
    required_memory_mb: int = 512
    expected_duration: float = 10.0
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    node_id: Optional[str] = None

    # Fields used by the recursive split logic
    start_idx: int = 0
    end_idx: int = 0

    def __post_init__(self) -> None:
        if self.end_idx == 0 and self.iterations:
            self.end_idx = self.iterations

@dataclass
class ExecutionRun:
    id: str
    timestamp: datetime
    node_count: int
    granularity: str
    injected_latency_ms: float
    packet_loss_rate: float
    throughput_ops: float
    latency_ms: float
    status: TaskStatus = TaskStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "node_count": self.node_count,
            "granularity": self.granularity,
            "injected_latency_ms": self.injected_latency_ms,
            "packet_loss_rate": self.packet_loss_rate,
            "throughput_ops": self.throughput_ops,
            "latency_ms": self.latency_ms,
            "status": self.status.value,
        }
