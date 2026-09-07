from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Enum representing the confidence level of LLM code detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class LLMCodeDetectionResult:
    """
    Data class representing the result of detecting LLM-generated code in a PR diff.
    
    Attributes:
        pr_id: Unique identifier for the pull request.
        file_path: Path to the file within the repository.
        line_start: Starting line number of the suspected LLM-generated code block.
        line_end: Ending line number of the suspected LLM-generated code block.
        confidence: Confidence level of the detection (High, Medium, Low, Unknown).
        confidence_score: Numeric score (0.0 to 1.0) supporting the confidence level.
        detection_method: String describing the heuristic or model used for detection.
        snippet_preview: Optional short preview of the detected code snippet.
        is_llm_generated: Boolean flag indicating if the code is flagged as LLM-generated.
        metadata: Additional dictionary for any extra context or raw scores.
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    confidence: ConfidenceLevel
    confidence_score: float
    detection_method: str
    snippet_preview: Optional[str] = None
    is_llm_generated: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "detection_method": self.detection_method,
            "snippet_preview": self.snippet_preview,
            "is_llm_generated": self.is_llm_generated,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert the dataclass instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMCodeDetectionResult":
        """
        Create an instance from a dictionary.
        
        Raises:
            ValueError: If required fields are missing or confidence is invalid.
        """
        required_fields = ["pr_id", "file_path", "line_start", "line_end", 
                           "confidence", "confidence_score", "detection_method"]
        
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        try:
            confidence_enum = ConfidenceLevel(data["confidence"])
        except ValueError:
            raise ValueError(f"Invalid confidence level: {data['confidence']}")

        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            confidence=confidence_enum,
            confidence_score=data["confidence_score"],
            detection_method=data["detection_method"],
            snippet_preview=data.get("snippet_preview"),
            is_llm_generated=data.get("is_llm_generated", True),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LLMCodeDetectionResult":
        """Create an instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
