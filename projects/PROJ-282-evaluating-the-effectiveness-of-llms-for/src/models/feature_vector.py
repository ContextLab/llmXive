"""
FeatureVector model generated from contracts/feature.schema.yaml.
Uses Pydantic to ensure schema compliance and prevent drift.
"""
from pydantic import BaseModel, Field
from typing import Optional
import json
import uuid
from datetime import datetime


class FeatureVector(BaseModel):
    """
    Pydantic model representing a feature vector extracted from a code snippet.
    Generated from contracts/feature.schema.yaml.
    """
    snippet_id: str = Field(..., description="Unique identifier for the code snippet")
    ast_depth: int = Field(..., ge=0, description="Depth of the Abstract Syntax Tree")
    cyclomatic_complexity: int = Field(..., ge=1, description="Cyclomatic complexity of the code")
    node_count: int = Field(..., ge=0, description="Total number of AST nodes")
    taint_api_count: int = Field(..., ge=0, description="Count of taint-source API calls")
    sanitization_present: bool = Field(..., description="Boolean presence of sanitization functions")
    embedding_similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score to vulnerability patterns")
    label_missing: bool = Field(False, description="Flag indicating if ground truth label is missing")

    class Config:
        json_schema_extra = {
            "example": {
                "snippet_id": "550e8400-e29b-41d4-a716-446655440000",
                "ast_depth": 5,
                "cyclomatic_complexity": 3,
                "node_count": 42,
                "taint_api_count": 1,
                "sanitization_present": False,
                "embedding_similarity_score": 0.85,
                "label_missing": False
            }
        }

    @classmethod
    def create_feature_vector(
        cls,
        snippet_id: Optional[str] = None,
        ast_depth: int = 0,
        cyclomatic_complexity: int = 1,
        node_count: int = 0,
        taint_api_count: int = 0,
        sanitization_present: bool = False,
        embedding_similarity_score: float = 0.0,
        label_missing: bool = False
    ) -> "FeatureVector":
        """
        Factory method to create a FeatureVector instance.
        Generates a UUID if snippet_id is not provided.
        """
        if snippet_id is None:
            snippet_id = str(uuid.uuid4())
        
        return cls(
            snippet_id=snippet_id,
            ast_depth=ast_depth,
            cyclomatic_complexity=cyclomatic_complexity,
            node_count=node_count,
            taint_api_count=taint_api_count,
            sanitization_present=sanitization_present,
            embedding_similarity_score=embedding_similarity_score,
            label_missing=label_missing
        )

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert the model to a JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureVector":
        """Create an instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureVector":
        """Create an instance from a JSON string."""
        return cls.model_validate_json(json_str)
