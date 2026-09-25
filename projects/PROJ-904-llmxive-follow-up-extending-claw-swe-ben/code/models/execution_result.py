"""
Execution Result Data Model.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json
from datetime import datetime

class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"

class FailureCategory(Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    OTHER = "other"

@dataclass
class ExecutionResult:
    instance_id: str
    model_size: str
    strategy: str
    status: ExecutionStatus
    prediction: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    context_tokens: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "model_size": self.model_size,
            "strategy": self.strategy,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            "prediction": self.prediction,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "context_tokens": self.context_tokens,
            "timestamp": self.timestamp or datetime.now().isoformat()
        }
