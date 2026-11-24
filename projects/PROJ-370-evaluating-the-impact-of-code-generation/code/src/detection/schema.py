from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

# Import the Severity enum defined in the extraction schema.
# This avoids duplication and keeps a single source of truth for severity levels.
from code.src.extraction.schema import Severity


class ConfidenceLevel(Enum):
    """Confidence levels for LLM code detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class LLMCodeDetectionResult:
    """Result of LLM-generated code detection for a single PR."""
    pr_id: str
    repo: str
    llm_code_flag: bool
    confidence: ConfidenceLevel
    matched_patterns: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'pr_id': self.pr_id,
            'repo': self.repo,
            'llm_code_flag': self.llm_code_flag,
            'confidence': self.confidence.value,
            'matched_patterns': self.matched_patterns,
            'file_paths': self.file_paths,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMCodeDetectionResult':
        """Create instance from dictionary."""
        return cls(
            pr_id=data['pr_id'],
            repo=data['repo'],
            llm_code_flag=data['llm_code_flag'],
            confidence=ConfidenceLevel(data['confidence']),
            matched_patterns=data.get('matched_patterns', []),
            file_paths=data.get('file_paths', []),
            error_message=data.get('error_message')
        )


@dataclass
class BugDetection:
    """
    Represents a detected bug within a PR diff.

    Attributes:
        pr_id: ID of the PR where the bug was found
        file_path: Path to the file containing the bug
        line_start: Starting line number of the bug
        line_end: Ending line number of the bug
        severity: Severity level of the bug
        description: Text description of the bug
        detection_method: Method used to detect (e.g., "llm", "heuristic", "human")
        confidence: Confidence score (0.0 to 1.0)
        is_confirmed: Whether the bug has been confirmed by human review
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    severity: Severity
    description: str
    detection_method: str
    confidence: float = 0.0
    is_confirmed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert BugDetection to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "severity": str(self.severity),
            "description": self.description,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "is_confirmed": self.is_confirmed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugDetection":
        """Create a BugDetection instance from a dictionary."""
        severity_str = data.get("severity", "info")
        if isinstance(severity_str, str):
            severity = Severity.from_string(severity_str)
        else:
            severity = severity_str

        return cls(
            pr_id=data.get("pr_id", ""),
            file_path=data.get("file_path", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            severity=severity,
            description=data.get("description", ""),
            detection_method=data.get("detection_method", "unknown"),
            confidence=data.get("confidence", 0.0),
            is_confirmed=data.get("is_confirmed", False),
        )

    def to_json(self) -> str:
        """Serialize BugDetection to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "BugDetection":
        """Deserialize BugDetection from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
