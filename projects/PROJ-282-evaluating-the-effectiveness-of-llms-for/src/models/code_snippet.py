"""
CodeSnippet dataclass generated from contracts/dataset.schema.yaml.

This module is auto-generated to prevent schema drift.
Fields are derived directly from the contract specification.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid
import json
from pathlib import Path
import re

@dataclass
class CodeSnippet:
    """
    Represents a single code snippet with metadata for vulnerability analysis.
    
    Generated from contracts/dataset.schema.yaml.
    DO NOT manually modify fields - regenerate from contract if schema changes.
    """
    snippet_id: str
    source_dataset: str
    file_path: str
    language: str
    code: str
    line_start: int
    line_end: int
    label: str
    category: Optional[str] = None
    context: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None

    # Validation constants from schema
    VALID_DATASETS = {"VulDeePecker", "BigVul", "Juliet_C", "Juliet_Java"}
    VALID_LANGUAGES = {"Python", "C", "JavaScript", "Java"}
    VALID_LABELS = {"vulnerable", "safe", "unknown"}
    UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

    def __post_init__(self):
        """Validate fields against schema constraints."""
        # Validate snippet_id format
        if not self.UUID_PATTERN.match(self.snippet_id):
            raise ValueError(f"Invalid snippet_id format: {self.snippet_id}")
        
        # Validate source_dataset
        if self.source_dataset not in self.VALID_DATASETS:
            raise ValueError(f"Invalid source_dataset: {self.source_dataset}. Must be one of {self.VALID_DATASETS}")
        
        # Validate language
        if self.language not in self.VALID_LANGUAGES:
            raise ValueError(f"Invalid language: {self.language}. Must be one of {self.VALID_LANGUAGES}")
        
        # Validate label
        if self.label not in self.VALID_LABELS:
            raise ValueError(f"Invalid label: {self.label}. Must be one of {self.VALID_LABELS}")
        
        # Validate line numbers
        if self.line_start < 1:
            raise ValueError(f"line_start must be >= 1, got {self.line_start}")
        if self.line_end < self.line_start:
            raise ValueError(f"line_end ({self.line_end}) must be >= line_start ({self.line_start})")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "snippet_id": self.snippet_id,
            "source_dataset": self.source_dataset,
            "file_path": self.file_path,
            "language": self.language,
            "code": self.code,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "label": self.label,
            "category": self.category,
            "context": self.context,
            "raw_metadata": self.raw_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSnippet":
        """Create instance from dictionary."""
        return cls(
            snippet_id=data["snippet_id"],
            source_dataset=data["source_dataset"],
            file_path=data["file_path"],
            language=data["language"],
            code=data["code"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            label=data["label"],
            category=data.get("category"),
            context=data.get("context"),
            raw_metadata=data.get("raw_metadata")
        )

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "CodeSnippet":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

def create_snippet(
    source_dataset: str,
    file_path: str,
    language: str,
    code: str,
    line_start: int,
    line_end: int,
    label: str,
    snippet_id: Optional[str] = None,
    category: Optional[str] = None,
    context: Optional[str] = None,
    raw_metadata: Optional[Dict[str, Any]] = None
) -> CodeSnippet:
    """
    Factory function to create a CodeSnippet with auto-generated ID.
    
    Args:
        source_dataset: Name of the source dataset
        file_path: Original file path
        language: Programming language
        code: Code content
        line_start: Starting line number
        line_end: Ending line number
        label: Ground truth label
        snippet_id: Optional custom ID (auto-generated if None)
        category: Optional vulnerability category
        context: Optional surrounding context
        raw_metadata: Optional additional metadata
        
    Returns:
        Validated CodeSnippet instance
    """
    if snippet_id is None:
        snippet_id = str(uuid.uuid4())
    
    return CodeSnippet(
        snippet_id=snippet_id,
        source_dataset=source_dataset,
        file_path=file_path,
        language=language,
        code=code,
        line_start=line_start,
        line_end=line_end,
        label=label,
        category=category,
        context=context,
        raw_metadata=raw_metadata
    )
