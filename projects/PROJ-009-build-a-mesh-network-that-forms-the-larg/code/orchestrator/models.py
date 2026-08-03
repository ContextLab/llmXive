"""
Data model classes for PhysicalNode, TaskChunk, and ExecutionRun.
Implements T008.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json
from pathlib import Path

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
    id: str
    hostname: str
    ip_address: str
    status: NodeStatus = NodeStatus.ONLINE
    available_memory_mb: int = 4096
    cpu_cores: int = 4
    last_heartbeat: Optional[datetime] = None

@dataclass
class TaskChunk:
    id: str
    payload: Any
    required_memory_mb: int = 512
    expected_duration: float = 10.0
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    node_id: Optional[str] = None

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
            "status": self.status.value
        }
