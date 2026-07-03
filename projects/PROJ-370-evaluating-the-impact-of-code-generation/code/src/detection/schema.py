"""
Schema definitions for LLM code detection results.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Confidence levels for LLM code detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNCERTAIN = "uncertain"


@dataclass
class LLMCodeDetectionResult:
    """
    Result of detecting LLM-generated code in a PR diff.

    Attributes:
        pr_id: Unique identifier for the pull request.
        file_path: Path to the file within the PR.
        line_start: Starting line number of the detected code snippet.
        line_end: Ending line number of the detected code snippet.
        detected: Boolean flag indicating if LLM-generated code was found.
        confidence: Confidence level of the detection (low, medium, high, uncertain).
        heuristic_name: Name of the heuristic or method used for detection.
        heuristic_details: Dictionary containing details about the heuristic match.
        raw_snippet: Optional raw text snippet of the detected code.
        metadata: Additional metadata for the detection event.
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    detected: bool
    confidence: ConfidenceLevel
    heuristic_name: str
    heuristic_details: Dict[str, Any] = field(default_factory=dict)
    raw_snippet: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the detection result to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "detected": self.detected,
            "confidence": self.confidence.value,
            "heuristic_name": self.heuristic_name,
            "heuristic_details": self.heuristic_details,
            "raw_snippet": self.raw_snippet,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the detection result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMCodeDetectionResult":
        """Create an LLMCodeDetectionResult instance from a dictionary."""
        confidence_val = data.get("confidence")
        if isinstance(confidence_val, str):
            confidence_val = ConfidenceLevel(confidence_val)
        elif confidence_val is None:
            confidence_val = ConfidenceLevel.UNCERTAIN

        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            detected=data["detected"],
            confidence=confidence_val,
            heuristic_name=data.get("heuristic_name", "unknown"),
            heuristic_details=data.get("heuristic_details", {}),
            raw_snippet=data.get("raw_snippet"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LLMCodeDetectionResult":
        """Create an LLMCodeDetectionResult instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
