from dataclasses import dataclass, field
from typing import Optional, Tuple, List
import json
from pathlib import Path

@dataclass
class CodeSample:
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

@dataclass
class SmellMetric:
    sample_id: str
    smell_type: str
    count: int
    threshold_used: float
    continuous_metric_value: float

@dataclass
class StatResult:
    smell_type: str
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    correction_method: str
    test_method_used: str
