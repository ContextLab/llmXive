from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json

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
