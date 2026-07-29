"""
FeatureVector Dataclass Implementation.

This module is GENERATED from contracts/feature.schema.yaml.
Do NOT manually modify field definitions to prevent schema drift.
"""
from dataclasses import dataclass, field
from typing import Optional, List
import uuid
from datetime import datetime
import json

# Constants for schema versioning to detect drift
_SCHEMA_VERSION = "1.0.0"
_EXPECTED_FIELDS = {
    "feature_vector_id",
    "snippet_id",
    "language",
    "ast_depth",
    "ast_node_count",
    "cyclomatic_complexity",
    "lines_of_code",
    "taint_source_count",
    "taint_sink_count",
    "has_sanitization",
    "embedding_similarity_score",
    "extraction_timestamp",
    "parser_version"
}

@dataclass
class FeatureVector:
    """
    Aggregated features for a code snippet including structural, semantic,
    and embedding-based metrics used for vulnerability prediction analysis.
    
    Generated from: contracts/feature.schema.yaml
    """
    feature_vector_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snippet_id: str = ""
    language: str = ""
    
    # Structural Metrics
    ast_depth: Optional[float] = None
    ast_node_count: Optional[int] = None
    cyclomatic_complexity: Optional[int] = None
    lines_of_code: Optional[int] = None
    
    # Semantic Metrics
    taint_source_count: Optional[int] = None
    taint_sink_count: Optional[int] = None
    has_sanitization: Optional[bool] = None
    
    # Embedding Metrics
    embedding_similarity_score: Optional[float] = None
    
    # Metadata
    extraction_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    parser_version: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert the FeatureVector to a dictionary."""
        return {
            "feature_vector_id": self.feature_vector_id,
            "snippet_id": self.snippet_id,
            "language": self.language,
            "ast_depth": self.ast_depth,
            "ast_node_count": self.ast_node_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "lines_of_code": self.lines_of_code,
            "taint_source_count": self.taint_source_count,
            "taint_sink_count": self.taint_sink_count,
            "has_sanitization": self.has_sanitization,
            "embedding_similarity_score": self.embedding_similarity_score,
            "extraction_timestamp": self.extraction_timestamp,
            "parser_version": self.parser_version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeatureVector":
        """Create a FeatureVector from a dictionary."""
        # Validate required fields
        if "snippet_id" not in data:
            raise ValueError("snippet_id is required")
        if "language" not in data:
            raise ValueError("language is required")
        
        return cls(
            feature_vector_id=data.get("feature_vector_id", str(uuid.uuid4())),
            snippet_id=data["snippet_id"],
            language=data["language"],
            ast_depth=data.get("ast_depth"),
            ast_node_count=data.get("ast_node_count"),
            cyclomatic_complexity=data.get("cyclomatic_complexity"),
            lines_of_code=data.get("lines_of_code"),
            taint_source_count=data.get("taint_source_count"),
            taint_sink_count=data.get("taint_sink_count"),
            has_sanitization=data.get("has_sanitization"),
            embedding_similarity_score=data.get("embedding_similarity_score"),
            extraction_timestamp=data.get("extraction_timestamp", datetime.utcnow().isoformat()),
            parser_version=data.get("parser_version")
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "FeatureVector":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def validate_schema(self) -> bool:
        """
        Validate that this instance matches the expected schema.
        Returns True if valid, raises ValueError otherwise.
        """
        instance_dict = self.to_dict()
        actual_fields = set(instance_dict.keys())
        
        if actual_fields != _EXPECTED_FIELDS:
            missing = _EXPECTED_FIELDS - actual_fields
            extra = actual_fields - _EXPECTED_FIELDS
            raise ValueError(
                f"Schema drift detected. Missing: {missing}, Extra: {extra}"
            )
        
        return True

def create_feature_vector(
    snippet_id: str,
    language: str,
    ast_depth: Optional[float] = None,
    ast_node_count: Optional[int] = None,
    cyclomatic_complexity: Optional[int] = None,
    lines_of_code: Optional[int] = None,
    taint_source_count: Optional[int] = None,
    taint_sink_count: Optional[int] = None,
    has_sanitization: Optional[bool] = None,
    embedding_similarity_score: Optional[float] = None,
    parser_version: Optional[str] = None
) -> FeatureVector:
    """
    Factory function to create a FeatureVector with provided values.
    Automatically generates ID and timestamp.
    """
    return FeatureVector(
        snippet_id=snippet_id,
        language=language,
        ast_depth=ast_depth,
        ast_node_count=ast_node_count,
        cyclomatic_complexity=cyclomatic_complexity,
        lines_of_code=lines_of_code,
        taint_source_count=taint_source_count,
        taint_sink_count=taint_sink_count,
        has_sanitization=has_sanitization,
        embedding_similarity_score=embedding_similarity_score,
        parser_version=parser_version
    )
