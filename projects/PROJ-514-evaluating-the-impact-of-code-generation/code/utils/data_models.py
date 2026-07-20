from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import json
from pathlib import Path

@dataclass
class CodeSample:
    """
    Represents a single code sample (human or LLM generated).
    Corresponds to the 'Balanced Blocked Design' sample entity.
    """
    source_type: str  # 'human' or 'llm'
    repository_id: str
    issue_id: str
    task_id: str
    language: str
    file_path: str
    function_name: str
    is_fresh_commit: bool
    content: str = ""
    sample_id: str = field(default="")
    commit_sha: str = field(default="")

    def to_dict(self) -> dict:
        """Converts the dataclass instance to a dictionary for JSON serialization."""
        return {
            "source_type": self.source_type,
            "repository_id": self.repository_id,
            "issue_id": self.issue_id,
            "task_id": self.task_id,
            "language": self.language,
            "file_path": self.file_path,
            "function_name": self.function_name,
            "is_fresh_commit": self.is_fresh_commit,
            "sample_id": self.sample_id,
            "commit_sha": self.commit_sha,
            "content_length": len(self.content)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CodeSample':
        """Reconstructs a CodeSample instance from a dictionary."""
        return cls(
            source_type=data.get("source_type", ""),
            repository_id=data.get("repository_id", ""),
            issue_id=data.get("issue_id", ""),
            task_id=data.get("task_id", ""),
            language=data.get("language", ""),
            file_path=data.get("file_path", ""),
            function_name=data.get("function_name", ""),
            is_fresh_commit=data.get("is_fresh_commit", False),
            content=data.get("content", ""),
            sample_id=data.get("sample_id", ""),
            commit_sha=data.get("commit_sha", "")
        )

@dataclass
class SmellMetric:
    """
    Represents a specific code smell metric detected in a sample.
    Maps to PMD violations or calculated metrics.
    """
    sample_id: str
    smell_type: str  # e.g., 'LongMethod', 'DuplicatedCode', 'FeatureEnvy', 'LongParameterList'
    count: int
    threshold_used: float
    continuous_metric_value: float

    def to_dict(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "smell_type": self.smell_type,
            "count": self.count,
            "threshold_used": self.threshold_used,
            "continuous_metric_value": self.continuous_metric_value
        }

@dataclass
class StatResult:
    """
    Represents the outcome of a statistical comparison test.
    Used for Blocked Permutation Test results.
    """
    smell_type: str
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    correction_method: str  # e.g., 'bonferroni'
    test_method_used: str   # e.g., 'blocked_permutation'

    def to_dict(self) -> dict:
        return {
            "smell_type": self.smell_type,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "correction_method": self.correction_method,
            "test_method_used": self.test_method_used
        }
