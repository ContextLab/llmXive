"""
FeatureVector model generated from contracts/feature.schema.yaml.
Ensures schema drift prevention by deriving fields from the contract.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import uuid
from datetime import datetime
import json
import re

from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class FeatureVectorSchema(BaseModel):
    """Pydantic schema generated from contracts/feature.schema.yaml."""
    ast_depth: int = Field(..., description="Depth of the Abstract Syntax Tree")
    cyclomatic_complexity: int = Field(..., description="Cyclomatic complexity metric")
    node_count: int = Field(..., description="Total number of AST nodes")
    taint_api_count: int = Field(..., description="Count of taint-source API calls")
    sanitization_present: bool = Field(..., description="Boolean flag for sanitization presence")
    embedding_similarity_score: float = Field(..., description="Similarity score against vulnerability patterns")

    class Config:
        json_schema_extra = {
            "example": {
                "ast_depth": 10,
                "cyclomatic_complexity": 5,
                "node_count": 150,
                "taint_api_count": 2,
                "sanitization_present": True,
                "embedding_similarity_score": 0.85
            }
        }


@dataclass
class FeatureVector:
    """
    Dataclass representation of a feature vector for a code snippet.
    Generated from contracts/feature.schema.yaml to prevent schema drift.
    """
    ast_depth: int
    cyclomatic_complexity: int
    node_count: int
    taint_api_count: int
    sanitization_present: bool
    embedding_similarity_score: float
    snippet_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert the FeatureVector to a dictionary."""
        return {
            "snippet_id": self.snippet_id,
            "ast_depth": self.ast_depth,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "node_count": self.node_count,
            "taint_api_count": self.taint_api_count,
            "sanitization_present": self.sanitization_present,
            "embedding_similarity_score": self.embedding_similarity_score,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FeatureVector':
        """Create a FeatureVector from a dictionary."""
        # Handle datetime parsing if present
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def validate_from_schema(self) -> bool:
        """
        Validates that the dataclass instance matches the Pydantic schema.
        This enforces the contract defined in feature.schema.yaml.
        """
        try:
            # Convert to dict and validate via Pydantic
            FeatureVectorSchema(**self.to_dict())
            return True
        except Exception:
            return False


def create_feature_vector(
    ast_depth: int,
    cyclomatic_complexity: int,
    node_count: int,
    taint_api_count: int,
    sanitization_present: bool,
    embedding_similarity_score: float,
    snippet_id: Optional[str] = None
) -> FeatureVector:
    """
    Factory function to create a FeatureVector instance.
    Ensures all required fields from the schema are provided.
    """
    return FeatureVector(
        ast_depth=ast_depth,
        cyclomatic_complexity=cyclomatic_complexity,
        node_count=node_count,
        taint_api_count=taint_api_count,
        sanitization_present=sanitization_present,
        embedding_similarity_score=embedding_similarity_score,
        snippet_id=snippet_id or str(uuid.uuid4())
    )
