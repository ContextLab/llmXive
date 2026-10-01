from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Confidence levels for LLM code detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_string(cls, value: str) -> "ConfidenceLevel":
        """Convert string to ConfidenceLevel enum."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid confidence level: {value}")


@dataclass
class LLMCodeDetectionResult:
    """
    Result of detecting LLM-generated code in a pull request diff.

    Attributes:
        pr_id: Unique identifier for the pull request.
        file_path: Path to the file containing the potential LLM-generated code.
        line_start: Starting line number of the detected code block.
        line_end: Ending line number of the detected code block.
        confidence: Confidence level of the detection.
        detection_method: Method used for detection (e.g., "heuristic", "model").
        is_llm_generated: Boolean flag indicating if code is likely LLM-generated.
        metadata: Additional metadata about the detection.
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    confidence: ConfidenceLevel
    detection_method: str
    is_llm_generated: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the detection result to a dictionary."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "confidence": self.confidence.value,
            "detection_method": self.detection_method,
            "is_llm_generated": self.is_llm_generated,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert the detection result to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMCodeDetectionResult":
        """Create an LLMCodeDetectionResult from a dictionary."""
        confidence_str = data.get("confidence")
        if not confidence_str:
            raise ValueError("Missing required field: confidence")

        try:
            confidence = ConfidenceLevel.from_string(confidence_str)
        except ValueError as e:
            raise ValueError(f"Invalid confidence level: {confidence_str}") from e

        required_fields = ["pr_id", "file_path", "line_start", "line_end", "detection_method", "is_llm_generated"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            confidence=confidence,
            detection_method=data["detection_method"],
            is_llm_generated=data["is_llm_generated"],
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LLMCodeDetectionResult":
        """Create an LLMCodeDetectionResult from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
