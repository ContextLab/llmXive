from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum

class CodeSnippetLanguageEnum(Enum):
    """Enum for language."""
    C = "C"
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"

class CodeSnippetSchema(BaseModel):
    """Auto-generated schema for CodeSnippet."""

    id: str = Field(..., description="id")
    language: CodeSnippetLanguageEnum = Field(..., description="language")
    source_code: str = Field(..., description="source_code")
    ground_truth_label: str = Field(..., description="ground_truth_label")
    ground_truth_category: str = Field(..., description="ground_truth_category")

class CodeSnippet(CodeSnippetSchema):
    """Concrete model class for CodeSnippet."""

def create_codesnippet(**kwargs) -> CodeSnippet:
    """Factory function to create a CodeSnippet instance."""
    return CodeSnippet(**kwargs)
