from dataclasses import dataclass, field
from typing import Optional, List
import uuid


@dataclass
class FeatureVector:
    """
    Dataclass representing the extracted feature vector for a code snippet.
    
    Attributes:
        id: Unique identifier for this feature vector instance.
        ast_depth: Maximum depth of the Abstract Syntax Tree (AST).
        cyclomatic_complexity: Cyclomatic complexity metric of the code.
        node_count: Total number of nodes in the AST.
        taint_api_count: Count of identified taint-source API calls.
        sanitization_present: Boolean flag indicating if sanitization functions were detected.
        embedding_similarity_score: List of similarity scores against canonical vulnerability patterns.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ast_depth: Optional[int] = None
    cyclomatic_complexity: Optional[int] = None
    node_count: Optional[int] = None
    taint_api_count: Optional[int] = None
    sanitization_present: Optional[bool] = None
    embedding_similarity_score: Optional[List[float]] = field(default_factory=list)


def create_feature_vector(
    ast_depth: Optional[int] = None,
    cyclomatic_complexity: Optional[int] = None,
    node_count: Optional[int] = None,
    taint_api_count: Optional[int] = None,
    sanitization_present: Optional[bool] = None,
    embedding_similarity_score: Optional[List[float]] = None
) -> FeatureVector:
    """
    Factory function to create a FeatureVector instance with validation.
    
    Args:
        ast_depth: AST depth value.
        cyclomatic_complexity: Cyclomatic complexity value.
        node_count: AST node count value.
        taint_api_count: Taint API count value.
        sanitization_present: Sanitization presence flag.
        embedding_similarity_score: List of similarity scores.
        
    Returns:
        A new FeatureVector instance.
        
    Raises:
        ValueError: If embedding_similarity_score is provided but not a list.
    """
    if embedding_similarity_score is not None and not isinstance(embedding_similarity_score, list):
        raise ValueError("embedding_similarity_score must be a list of floats or None")
        
    return FeatureVector(
        ast_depth=ast_depth,
        cyclomatic_complexity=cyclomatic_complexity,
        node_count=node_count,
        taint_api_count=taint_api_count,
        sanitization_present=sanitization_present,
        embedding_similarity_score=embedding_similarity_score if embedding_similarity_score is not None else []
    )
