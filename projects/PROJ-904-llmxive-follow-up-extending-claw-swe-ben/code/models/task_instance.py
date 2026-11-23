from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import json

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskInstance:
    instance_id: str
    repo: str
    issue_description: str
    test_patch: str
    line_count: int
    files_in_context: List[str]
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "issue_description": self.issue_description,
            "test_patch": self.test_patch,
            "line_count": self.line_count,
            "files_in_context": self.files_in_context,
            "status": self.status.value,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskInstance":
        return cls(
            instance_id=data["instance_id"],
            repo=data["repo"],
            issue_description=data["issue_description"],
            test_patch=data["test_patch"],
            line_count=data["line_count"],
            files_in_context=data["files_in_context"],
            status=TaskStatus(data.get("status", "pending")),
            error_message=data.get("error_message"),
        )

    def compute_hash(self) -> str:
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
