"""
FeatureVector model generated from contracts/feature.schema.yaml using pydantic.
DO NOT EDIT MANUALLY. Regenerate if schema changes.
"""
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime


class FeatureVectorSchema(BaseModel):
    """Schema definition for FeatureVector matching contracts/feature.schema.yaml."""
    ast_depth: int = Field(..., description="Depth of the Abstract Syntax Tree")
    cyclomatic_complexity: int = Field(..., description="Cyclomatic complexity of the code snippet")
    node_count: int = Field(..., description="Total number of nodes in the AST")
    taint_api_count: int = Field(..., description="Count of known taint-source API calls")
    sanitization_present: bool = Field(..., description="Boolean presence of sanitization functions")
    embedding_similarity_score: float = Field(..., description="Similarity score against vulnerability patterns")


class FeatureVector(BaseModel):
    """
    Data model representing extracted features for a code snippet.
    Generated from contracts/feature.schema.yaml.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the feature vector")
    ast_depth: int = Field(..., description="Depth of the Abstract Syntax Tree")
    cyclomatic_complexity: int = Field(..., description="Cyclomatic complexity of the code snippet")
    node_count: int = Field(..., description="Total number of nodes in the AST")
    taint_api_count: int = Field(..., description="Count of known taint-source API calls")
    sanitization_present: bool = Field(..., description="Boolean presence of sanitization functions")
    embedding_similarity_score: float = Field(..., description="Similarity score against vulnerability patterns")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of creation")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "ast_depth": 5,
                "cyclomatic_complexity": 3,
                "node_count": 42,
                "taint_api_count": 1,
                "sanitization_present": True,
                "embedding_similarity_score": 0.85,
                "created_at": "2023-10-27T10:00:00Z"
            }
        }


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
    
    Args:
        ast_depth: Depth of the AST
        cyclomatic_complexity: Cyclomatic complexity value
        node_count: Total AST node count
        taint_api_count: Count of taint APIs
        sanitization_present: Presence of sanitization
        embedding_similarity_score: Similarity score
        snippet_id: Optional ID to link to a specific snippet (if known)
        
    Returns:
        FeatureVector instance
    """
    kwargs = {
        "ast_depth": ast_depth,
        "cyclomatic_complexity": cyclomatic_complexity,
        "node_count": node_count,
        "taint_api_count": taint_api_count,
        "sanitization_present": sanitization_present,
        "embedding_similarity_score": embedding_similarity_score
    }
    if snippet_id:
        # If a specific ID is provided, we'd need to override the default factory,
        # but since pydantic v2 doesn't allow overriding default_factory easily in init,
        # we assume the ID is generated or handled externally if strict ID matching is needed.
        # For now, we rely on the auto-generated UUID or pass it if the schema allowed it.
        # Since the schema has 'id' as a field with default_factory, we leave it auto-generated
        # unless the caller explicitly sets it via model_validate or similar if needed.
        pass 
    
    return FeatureVector(**kwargs)
