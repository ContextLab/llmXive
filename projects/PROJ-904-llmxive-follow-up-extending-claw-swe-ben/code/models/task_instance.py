"""
TaskInstance data model for the llmXive Context Fidelity vs. Model Scaling pipeline.

This module defines the core data structure representing a single task instance
from the Claw-SWE-Bench dataset, including its metadata, issue description,
and associated file context.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import json


class TaskStatus(Enum):
    """Enumeration of possible execution statuses for a task instance."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskInstance:
    """
    Represents a single task instance from the benchmark.

    Attributes:
        instance_id: Unique identifier for the task instance.
        repo: Repository name (e.g., 'django/django').
        base_commit: Git commit hash for the base state.
        patch: The gold patch (solution) if available.
        test_patch: The test patch to evaluate the solution.
        problem_statement: Natural language description of the issue.
        hints: List of hints provided for the task.
        files: Dictionary mapping file paths to their content in the base state.
        resolved: Boolean indicating if the instance was resolved (if known).
        status: Current execution status.
        created_at: Timestamp of creation (ISO format string).
        metadata: Additional arbitrary metadata.
    """
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: Optional[str] = None
    test_patch: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)
    resolved: Optional[bool] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and initialize derived fields."""
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")
        if not self.repo:
            raise ValueError("repo cannot be empty")
        if not self.base_commit:
            raise ValueError("base_commit cannot be empty")
        if not self.problem_statement:
            raise ValueError("problem_statement cannot be empty")
        
        # Ensure lists and dicts are mutable copies
        self.hints = list(self.hints)
        self.files = dict(self.files)
        self.metadata = dict(self.metadata)

    def get_content_hash(self) -> str:
        """
        Generate a deterministic hash of the instance's core content.
        
        This is useful for caching, deduplication, or verifying data integrity.
        """
        content_dict = {
            "repo": self.repo,
            "base_commit": self.base_commit,
            "problem_statement": self.problem_statement,
            "files": self.files,
            "patch": self.patch,
            "test_patch": self.test_patch,
        }
        # Sort keys for deterministic serialization
        serialized = json.dumps(content_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary for serialization."""
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "patch": self.patch,
            "test_patch": self.test_patch,
            "problem_statement": self.problem_statement,
            "hints": self.hints,
            "files": self.files,
            "resolved": self.resolved,
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskInstance":
        """
        Create a TaskInstance from a dictionary.
        
        Args:
            data: Dictionary containing instance data.
            
        Returns:
            A new TaskInstance object.
        """
        status_value = data.get("status", "pending")
        if isinstance(status_value, str):
            try:
                status = TaskStatus(status_value)
            except ValueError:
                status = TaskStatus.PENDING
        else:
            status = status_value
        
        return cls(
            instance_id=data["instance_id"],
            repo=data["repo"],
            base_commit=data["base_commit"],
            patch=data.get("patch"),
            test_patch=data.get("test_patch"),
            problem_statement=data["problem_statement"],
            hints=data.get("hints", []),
            files=data.get("files", {}),
            resolved=data.get("resolved"),
            status=status,
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"TaskInstance(id={self.instance_id}, repo={self.repo}, status={self.status.value})"

    def __repr__(self) -> str:
        return (
            f"TaskInstance(instance_id={self.instance_id!r}, repo={self.repo!r}, "
            f"base_commit={self.base_commit!r}, status={self.status!r})"
        )
