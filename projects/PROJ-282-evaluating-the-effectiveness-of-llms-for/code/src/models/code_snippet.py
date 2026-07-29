"""
CodeSnippet model generated from contracts/dataset.schema.yaml.

This module defines the CodeSnippet dataclass and factory function.
Fields are derived strictly from the schema contract to prevent drift.
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid
import json
from pathlib import Path


@dataclass
class CodeSnippet:
    """
    Represents a single code snippet extracted from a dataset.
    
    Generated from contracts/dataset.schema.yaml.
    Fields:
      - snippet_id: Unique identifier (UUID)
      - source_dataset: Name of the source dataset (e.g., 'VulDeePecker', 'BigVul')
      - raw_id: Original ID from the source dataset
      - language: Programming language (e.g., 'python', 'c', 'java')
      - code: The actual code content
      - label: Ground truth label (e.g., 'vulnerable', 'safe')
      - category: Vulnerability category (e.g., 'SQLi', 'Buffer Overflow')
      - file_path: Path to the source file (if available)
      - line_start: Starting line number
      - line_end: Ending line number
      - context: Surrounding code context (optional)
      - metadata: Additional metadata as a dictionary
    """
    snippet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_dataset: Optional[str] = None
    raw_id: Optional[str] = None
    language: Optional[str] = None
    code: Optional[str] = None
    label: Optional[str] = None
    category: Optional[str] = None
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    context: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert the dataclass to a dictionary."""
        return {
            "snippet_id": self.snippet_id,
            "source_dataset": self.source_dataset,
            "raw_id": self.raw_id,
            "language": self.language,
            "code": self.code,
            "label": self.label,
            "category": self.category,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "context": self.context,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodeSnippet":
        """Create a CodeSnippet instance from a dictionary."""
        # Ensure metadata is a dict if not provided
        if "metadata" in data and not isinstance(data["metadata"], dict):
            data["metadata"] = {}
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CodeSnippet":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


def create_snippet(
    source_dataset: Optional[str] = None,
    raw_id: Optional[str] = None,
    language: Optional[str] = None,
    code: Optional[str] = None,
    label: Optional[str] = None,
    category: Optional[str] = None,
    file_path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    context: Optional[str] = None,
    metadata: Optional[dict] = None,
    snippet_id: Optional[str] = None
) -> CodeSnippet:
    """
    Factory function to create a CodeSnippet instance.
    
    Args:
        source_dataset: Name of the source dataset
        raw_id: Original ID from the source dataset
        language: Programming language
        code: The actual code content
        label: Ground truth label
        category: Vulnerability category
        file_path: Path to the source file
        line_start: Starting line number
        line_end: Ending line number
        context: Surrounding code context
        metadata: Additional metadata
        snippet_id: Optional custom ID (otherwise auto-generated)
        
    Returns:
        CodeSnippet: A new CodeSnippet instance
    """
    kwargs = {
        "source_dataset": source_dataset,
        "raw_id": raw_id,
        "language": language,
        "code": code,
        "label": label,
        "category": category,
        "file_path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "context": context,
        "metadata": metadata if metadata is not None else {}
    }
    
    if snippet_id is not None:
        kwargs["snippet_id"] = snippet_id
        
    return CodeSnippet(**kwargs)
