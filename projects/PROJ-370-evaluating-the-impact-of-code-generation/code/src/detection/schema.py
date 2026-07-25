from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

class ConfidenceLevel(Enum):
    """Confidence levels for LLM code detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSURE = "unsure"

@dataclass
class LLMCodeDetectionResult:
    """
    Result of detecting LLM-generated code in a diff.
    
    Attributes:
        pr_id: The PR identifier
        file_path: The file path being analyzed
        llm_code_flag: Boolean indicating if LLM code was detected
        confidence: Confidence level of the detection
        detection_reason: Human-readable explanation of the detection
        heuristic_score: Numerical score from heuristic analysis
        matched_patterns: List of regex patterns that matched
    """
    pr_id: str
    file_path: str
    llm_code_flag: bool
    confidence: ConfidenceLevel
    detection_reason: str
    heuristic_score: float
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the detection result to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "llm_code_flag": self.llm_code_flag,
            "confidence": self.confidence.value,
            "detection_reason": self.detection_reason,
            "heuristic_score": self.heuristic_score,
            "matched_patterns": self.matched_patterns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMCodeDetectionResult':
        """Create a detection result from a dictionary."""
        confidence_value = data.get('confidence', 'unsure')
        try:
            confidence = ConfidenceLevel(confidence_value)
        except ValueError:
            confidence = ConfidenceLevel.UNSURE
        
        return cls(
            pr_id=data['pr_id'],
            file_path=data['file_path'],
            llm_code_flag=data['llm_code_flag'],
            confidence=confidence,
            detection_reason=data.get('detection_reason', ''),
            heuristic_score=data.get('heuristic_score', 0.0),
            matched_patterns=data.get('matched_patterns', [])
        )

    def to_json(self) -> str:
        """Convert the detection result to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'LLMCodeDetectionResult':
        """Create a detection result from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
