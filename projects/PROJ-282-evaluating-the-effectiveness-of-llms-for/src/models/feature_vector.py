"""
FeatureVector Model generated from contracts/feature.schema.yaml.

This file is auto-generated to prevent schema drift (Constitution Principle IV).
Do not manually edit fields; update the source contract and regenerate.
"""
from dataclasses import dataclass, field
from typing import Optional, List
import uuid
from datetime import datetime
import json

@dataclass
class FeatureVector:
    """
    Represents structural, semantic, and embedding features for a code snippet.
    Generated from: contracts/feature.schema.yaml
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snippet_id: Optional[str] = None
    ast_depth: int = 0
    cyclomatic_complexity: int = 0
    node_count: int = 0
    taint_api_count: int = 0
    sanitization_present: bool = False
    embedding_similarity_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert the FeatureVector to a dictionary for serialization."""
        return {
            "id": self.id,
            "snippet_id": self.snippet_id,
            "ast_depth": self.ast_depth,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "node_count": self.node_count,
            "taint_api_count": self.taint_api_count,
            "sanitization_present": self.sanitization_present,
            "embedding_similarity_score": self.embedding_similarity_score,
            "created_at": self.created_at
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the FeatureVector to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureVector":
        """Create a FeatureVector instance from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            snippet_id=data.get("snippet_id"),
            ast_depth=data.get("ast_depth", 0),
            cyclomatic_complexity=data.get("cyclomatic_complexity", 0),
            node_count=data.get("node_count", 0),
            taint_api_count=data.get("taint_api_count", 0),
            sanitization_present=data.get("sanitization_present", False),
            embedding_similarity_score=data.get("embedding_similarity_score", 0.0),
            created_at=data.get("created_at", datetime.utcnow().isoformat())
        )

def create_feature_vector(
    snippet_id: Optional[str] = None,
    ast_depth: int = 0,
    cyclomatic_complexity: int = 0,
    node_count: int = 0,
    taint_api_count: int = 0,
    sanitization_present: bool = False,
    embedding_similarity_score: float = 0.0
) -> FeatureVector:
    """
    Factory function to create a FeatureVector instance.
    
    Args:
        snippet_id: ID of the source code snippet.
        ast_depth: Maximum AST depth.
        cyclomatic_complexity: McCabe complexity score.
        node_count: Total AST node count.
        taint_api_count: Count of taint-source APIs.
        sanitization_present: Boolean flag for sanitization.
        embedding_similarity_score: Similarity to vulnerability patterns.
        
    Returns:
        A new FeatureVector instance.
    """
    return FeatureVector(
        snippet_id=snippet_id,
        ast_depth=ast_depth,
        cyclomatic_complexity=cyclomatic_complexity,
        node_count=node_count,
        taint_api_count=taint_api_count,
        sanitization_present=sanitization_present,
        embedding_similarity_score=embedding_similarity_score
    )
