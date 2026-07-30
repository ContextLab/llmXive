"""
CodeSnippet model generated from contracts/dataset.schema.yaml.

This file is auto-generated to prevent schema drift.
Source: contracts/dataset.schema.yaml
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any

@dataclass
class CodeSnippet:
    """
    Represents a code snippet with ground truth labels.
    
    Generated from: contracts/dataset.schema.yaml
    Fields:
        id: Unique identifier (UUID)
        language: Programming language
        source_code: Raw code content
        ground_truth_label: 'vulnerable', 'safe', or None
        ground_truth_category: Specific category or None
    """
    id: str
    language: str
    source_code: str
    ground_truth_label: Optional[str]
    ground_truth_category: Optional[str]

    def __post_init__(self):
        """Validate required fields and types."""
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.language:
            raise ValueError("language cannot be empty")
        if self.source_code is None:
            raise ValueError("source_code cannot be None")
        
        # Validate label enum if present
        valid_labels = ['vulnerable', 'safe', None]
        if self.ground_truth_label not in valid_labels:
            raise ValueError(f"ground_truth_label must be one of {valid_labels}, got {self.ground_truth_label}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "language": self.language,
            "source_code": self.source_code,
            "ground_truth_label": self.ground_truth_label,
            "ground_truth_category": self.ground_truth_category
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSnippet":
        """Create instance from dictionary."""
        return cls(
            id=data["id"],
            language=data["language"],
            source_code=data["source_code"],
            ground_truth_label=data.get("ground_truth_label"),
            ground_truth_category=data.get("ground_truth_category")
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CodeSnippet":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

def create_snippet(
    language: str,
    source_code: str,
    ground_truth_label: Optional[str] = None,
    ground_truth_category: Optional[str] = None,
    snippet_id: Optional[str] = None
) -> CodeSnippet:
    """
    Factory function to create a CodeSnippet instance.
    
    Args:
        language: Programming language
        source_code: Raw code content
        ground_truth_label: Optional label ('vulnerable' or 'safe')
        ground_truth_category: Optional vulnerability category
        snippet_id: Optional UUID, generated if not provided
    
    Returns:
        CodeSnippet instance
    """
    if snippet_id is None:
        snippet_id = str(uuid.uuid4())
    
    return CodeSnippet(
        id=snippet_id,
        language=language,
        source_code=source_code,
        ground_truth_label=ground_truth_label,
        ground_truth_category=ground_truth_category
    )
