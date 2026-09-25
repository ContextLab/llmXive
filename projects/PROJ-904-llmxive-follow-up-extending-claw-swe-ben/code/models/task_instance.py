"""
Task Instance Data Model.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import json

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskInstance:
    instance_id: str
    repo: str
    base_commit: str
    patch: str
    problem_statement: str
    hints: List[str] = field(default_factory=list)
    test_patch: str = ""
    relevant_files: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "patch": self.patch,
            "problem_statement": self.problem_statement,
            "hints": self.hints,
            "test_patch": self.test_patch,
            "relevant_files": self.relevant_files,
            "status": self.status.value
        }
