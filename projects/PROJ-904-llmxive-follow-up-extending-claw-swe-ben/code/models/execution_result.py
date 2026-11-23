from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json
from datetime import datetime

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class FailureCategory(str, Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"
    OTHER = "other"

@dataclass
class ExecutionResult:
    instance_id: str
    strategy: str
    model_size: str
    pass_at_1: bool
    duration_seconds: float
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    failure_category: Optional[FailureCategory] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "strategy": self.strategy,
            "model_size": self.model_size,
            "pass_at_1": self.pass_at_1,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "failure_category": self.failure_category.value if self.failure_category else None,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        return cls(
            instance_id=data["instance_id"],
            strategy=data["strategy"],
            model_size=data["model_size"],
            pass_at_1=data["pass_at_1"],
            duration_seconds=data["duration_seconds"],
            status=ExecutionStatus(data.get("status", "success")),
            failure_category=FailureCategory(data["failure_category"]) if data.get("failure_category") else None,
            error_message=data.get("error_message"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )

    def compute_hash(self) -> str:
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
