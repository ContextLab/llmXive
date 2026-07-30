"""
FeatureVector model generated from contracts/feature.schema.yaml.
Constraint: Do NOT manually implement fields; generated from contract to prevent schema drift.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import uuid
from datetime import datetime
import json
import re

@dataclass
class FeatureVector:
    """
    Generated from contracts/feature.schema.yaml.
    Represents structural, semantic, and embedding features for a code snippet.
    """
    id: str
    snippet_id: str
    language: str
    ast_depth: int
    cyclomatic_complexity: int
    node_count: int
    taint_api_count: int
    sanitization_present: bool
    embedding_similarity_score: float
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureVector":
        """Create instance from dictionary, validating required fields."""
        required = [
            "id", "snippet_id", "language", "ast_depth",
            "cyclomatic_complexity", "node_count",
            "taint_api_count", "sanitization_present",
            "embedding_similarity_score"
        ]
        for field_name in required:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        return cls(
            id=data["id"],
            snippet_id=data["snippet_id"],
            language=data["language"],
            ast_depth=int(data["ast_depth"]),
            cyclomatic_complexity=int(data["cyclomatic_complexity"]),
            node_count=int(data["node_count"]),
            taint_api_count=int(data["taint_api_count"]),
            sanitization_present=bool(data["sanitization_present"]),
            embedding_similarity_score=float(data["embedding_similarity_score"]),
            extracted_at=data.get("extracted_at", datetime.utcnow().isoformat())
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "FeatureVector":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """Validate field types and constraints based on schema."""
        if not isinstance(self.id, str) or not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', self.id):
            raise ValueError("Invalid UUID format for id")
        
        if not isinstance(self.snippet_id, str):
            raise ValueError("snippet_id must be a string")
        
        if not isinstance(self.language, str):
            raise ValueError("language must be a string")
        
        if not isinstance(self.ast_depth, int) or self.ast_depth < 0:
            raise ValueError("ast_depth must be a non-negative integer")
        
        if not isinstance(self.cyclomatic_complexity, int) or self.cyclomatic_complexity < 1:
            raise ValueError("cyclomatic_complexity must be an integer >= 1")
        
        if not isinstance(self.node_count, int) or self.node_count < 0:
            raise ValueError("node_count must be a non-negative integer")
        
        if not isinstance(self.taint_api_count, int) or self.taint_api_count < 0:
            raise ValueError("taint_api_count must be a non-negative integer")
        
        if not isinstance(self.sanitization_present, bool):
            raise ValueError("sanitization_present must be a boolean")
        
        if not isinstance(self.embedding_similarity_score, (int, float)):
            raise ValueError("embedding_similarity_score must be a number")
        
        if not -1.0 <= self.embedding_similarity_score <= 1.0:
            raise ValueError("embedding_similarity_score must be between -1.0 and 1.0")
        
        return True

def create_feature_vector(
    snippet_id: str,
    language: str,
    ast_depth: int,
    cyclomatic_complexity: int,
    node_count: int,
    taint_api_count: int,
    sanitization_present: bool,
    embedding_similarity_score: float,
    vector_id: Optional[str] = None
) -> FeatureVector:
    """
    Factory function to create a FeatureVector instance.
    Generates a UUID if not provided.
    """
    if vector_id is None:
        vector_id = str(uuid.uuid4())
    
    return FeatureVector(
        id=vector_id,
        snippet_id=snippet_id,
        language=language,
        ast_depth=ast_depth,
        cyclomatic_complexity=cyclomatic_complexity,
        node_count=node_count,
        taint_api_count=taint_api_count,
        sanitization_present=sanitization_present,
        embedding_similarity_score=embedding_similarity_score
    )