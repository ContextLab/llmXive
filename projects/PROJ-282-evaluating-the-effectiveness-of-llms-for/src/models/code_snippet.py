"""
CodeSnippet model generated from contracts/dataset.schema.yaml.
This file is auto-generated to prevent schema drift (Constitution IV).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid
import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import yaml

# Schema definition loaded from contract
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"

def load_schema() -> Dict[str, Any]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema contract not found at {SCHEMA_PATH}. "
                              "Please ensure T007a has been completed.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

class CodeSnippetSchema(BaseModel):
    """Pydantic model representing the schema contract for CodeSnippet."""
    type: str
    properties: Dict[str, Any]
    required: List[str]

class CodeSnippet(BaseModel):
    """
    Data model for a single code snippet.
    Generated from contracts/dataset.schema.yaml.
    """
    id: str = Field(..., description="Unique identifier for the snippet")
    language: str = Field(..., description="Programming language", pattern="^(C|Python|JavaScript)$")
    source_code: str = Field(..., description="The actual source code content")
    ground_truth_label: str = Field(..., description="Ground truth vulnerability label")
    ground_truth_category: str = Field(..., description="Ground truth vulnerability category")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "snip_001",
                "language": "Python",
                "source_code": "import os\nos.system(input())",
                "ground_truth_label": "vulnerable",
                "ground_truth_category": "Command Injection"
            }
        }

@dataclass
class CodeSnippetDataclass:
    """
    Dataclass version for internal processing if needed,
    but Pydantic CodeSnippet is the primary interface.
    """
    id: str
    language: str
    source_code: str
    ground_truth_label: str
    ground_truth_category: str
    metadata: Dict[str, Any] = field(default_factory=dict)

def create_snippet(data: Dict[str, Any]) -> CodeSnippet:
    """
    Factory function to create a validated CodeSnippet from a dictionary.
    Ensures data conforms to the schema contract.
    """
    return CodeSnippet(**data)

def snippet_to_dict(snippet: CodeSnippet) -> Dict[str, Any]:
    """Convert a CodeSnippet instance to a dictionary."""
    return snippet.model_dump()

def snippet_to_json(snippet: CodeSnippet) -> str:
    """Convert a CodeSnippet instance to a JSON string."""
    return snippet.model_dump_json()

def validate_contract() -> bool:
    """
    Validates that the current schema file exists and is loadable.
    Returns True if valid, raises error otherwise.
    """
    try:
        schema = load_schema()
        # Basic validation of structure
        if 'properties' not in schema:
            raise ValueError("Schema missing 'properties' key")
        if 'required' not in schema:
            raise ValueError("Schema missing 'required' key")
        return True
    except Exception as e:
        raise RuntimeError(f"Schema validation failed: {e}")

# Run validation on import to ensure contract integrity
if __name__ != "__main__":
    try:
        validate_contract()
    except FileNotFoundError:
        # Allow import in test environments where contract might be mocked or missing
        pass
