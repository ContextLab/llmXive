from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import hashlib
import json

class LabelType(Enum):
    """Enumeration for code block labels."""
    LLM = "LLM"
    HUMAN = "HUMAN"
    UNKNOWN = "UNKNOWN"

@dataclass
class Repository:
    """Represents a GitHub repository."""
    id: str
    full_name: str
    stargazers_count: int
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    description: Optional[str] = None

@dataclass
class CodeBlock:
    """Represents a code block (function/class) extracted from a repository."""
    repo_id: str
    file_path: str
    block_id: str
    start_line: int
    end_line: int
    label: Optional[LabelType] = None
    confidence: float = 0.0
    complexity: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MaintenanceEvent:
    """Represents a maintenance event (churn, bug fix) for a code block."""
    block_id: str
    repo_id: str
    event_type: str  # 'churn', 'bug_fix'
    timestamp: datetime
    lines_added: int = 0
    lines_deleted: int = 0
    issue_id: Optional[str] = None

@dataclass
class MatchedPair:
    """Represents a matched pair of LLM and Human code blocks."""
    llm_block_id: str
    human_block_id: str
    repo_id: str
    propensity_score_diff: float
    matched_at: datetime = field(default_factory=datetime.now)
    llm_metrics: Dict[str, Any] = field(default_factory=dict)
    human_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "llm_block_id": self.llm_block_id,
            "human_block_id": self.human_block_id,
            "repo_id": self.repo_id,
            "propensity_score_diff": self.propensity_score_diff,
            "matched_at": self.matched_at.isoformat(),
            "llm_metrics": self.llm_metrics,
            "human_metrics": self.human_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchedPair':
        """Create from dictionary."""
        return cls(
            llm_block_id=data["llm_block_id"],
            human_block_id=data["human_block_id"],
            repo_id=data["repo_id"],
            propensity_score_diff=data["propensity_score_diff"],
            matched_at=datetime.fromisoformat(data["matched_at"]),
            llm_metrics=data.get("llm_metrics", {}),
            human_metrics=data.get("human_metrics", {})
        )
