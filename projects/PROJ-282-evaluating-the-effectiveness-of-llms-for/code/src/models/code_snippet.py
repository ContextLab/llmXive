from dataclasses import dataclass, field
from typing import Optional
import uuid
import json
from pathlib import Path
from pydantic import BaseModel, Field, validator

# Schema definition matches contracts/dataset.schema.yaml
class CodeSnippetSchema(BaseModel):
    id: str = Field(..., description="Unique identifier")
    language: str = Field(..., enum=["C", "Python", "JavaScript"], description="Programming language")
    source_code: str = Field(..., description="The code snippet")
    ground_truth_label: str = Field(..., description="Label: vulnerable/safe")
    ground_truth_category: str = Field(..., description="Category: SQLi, XSS, etc.")

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "language": {"type": "string", "enum": ["C", "Python", "JavaScript"]},
                "source_code": {"type": "string"},
                "ground_truth_label": {"type": "string"},
                "ground_truth_category": {"type": "string"}
            },
            "required": ["id", "language", "source_code", "ground_truth_label", "ground_truth_category"]
        }

@dataclass
class CodeSnippet:
    id: str
    language: str
    source_code: str
    ground_truth_label: str
    ground_truth_category: str
    is_missing_label: bool = False

    def to_dict(self):
        return {
            "id": self.id,
            "language": self.language,
            "source_code": self.source_code,
            "ground_truth_label": self.ground_truth_label,
            "ground_truth_category": self.ground_truth_category,
            "is_missing_label": self.is_missing_label
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            language=data.get("language", "Unknown"),
            source_code=data.get("source_code", ""),
            ground_truth_label=data.get("ground_truth_label", "unknown"),
            ground_truth_category=data.get("ground_truth_category", "unknown"),
            is_missing_label=data.get("is_missing_label", False)
        )

def create_snippet(data: dict) -> CodeSnippet:
    """Factory function to create a CodeSnippet from a dictionary."""
    return CodeSnippet.from_dict(data)
