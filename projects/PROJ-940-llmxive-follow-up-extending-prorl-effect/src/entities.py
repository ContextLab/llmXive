"""
Entity definitions for the llmXive ProRL pipeline.

This module defines the core data structures used to represent items,
similarity relationships, recommendation paths, and evaluation metrics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np


class ItemNode:
    """
    Represents a single item in the recommendation graph.

    Attributes:
        item_id: Unique identifier for the item (e.g., ASIN, Movie ID).
        features: Dictionary of item features (genres, embeddings, etc.).
        metadata: Additional arbitrary metadata about the item.
    """

    def __init__(self, item_id: str, features: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.item_id: str = item_id
        self.features: Dict[str, Any] = features if features is not None else {}
        self.metadata: Dict[str, Any] = metadata if metadata is not None else {}

    def __repr__(self) -> str:
        return f"ItemNode(id={self.item_id}, features={list(self.features.keys())})"

    def __hash__(self) -> int:
        return hash(self.item_id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, ItemNode):
            return False
        return self.item_id == other.item_id


@dataclass
class SimilarityEdge:
    """
    Represents a weighted edge between two items based on similarity.

    Attributes:
        source_id: ID of the source item.
        target_id: ID of the target item.
        weight: Similarity score (e.g., cosine similarity) between 0.0 and 1.0.
        similarity_type: String indicating the method used (e.g., 'cosine', 'jaccard').
    """
    source_id: str
    target_id: str
    weight: float
    similarity_type: str = "cosine"

    def __post_init__(self):
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Edge weight must be between 0.0 and 1.0, got {self.weight}")

    def __repr__(self) -> str:
        return f"SimilarityEdge({self.source_id} -> {self.target_id}, w={self.weight:.4f})"


@dataclass
class RecommendationPath:
    """
    Represents a sequence of items recommended to a user, starting from a seed.

    Attributes:
        seed_id: The ID of the starting item (cold-start seed).
        path_items: Ordered list of item IDs in the recommendation path.
        scores: List of scores corresponding to each step in the path (after rectification).
        raw_scores: List of raw greedy scores before rectification (for comparison).
        path_length: The length of the path (number of steps).
        metadata: Additional context about how the path was generated.
    """
    seed_id: str
    path_items: List[str] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    raw_scores: List[float] = field(default_factory=list)
    path_length: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.path_length == 0:
            self.path_length = len(self.path_items)
        # Ensure consistency
        if len(self.path_items) != self.path_length:
            raise ValueError("path_length must match the number of items in path_items")
        if len(self.scores) != self.path_length:
            raise ValueError("scores list length must match path_length")
        if len(self.raw_scores) != self.path_length:
            raise ValueError("raw_scores list length must match path_length")

    def get_total_score(self) -> float:
        """Calculates the sum of rectified scores in the path."""
        return sum(self.scores) if self.scores else 0.0

    def get_average_score(self) -> float:
        """Calculates the average rectified score in the path."""
        return self.get_total_score() / self.path_length if self.path_length > 0 else 0.0

    def __repr__(self) -> str:
        return f"RecommendationPath(seed={self.seed_id}, len={self.path_length}, total_score={self.get_total_score():.4f})"


class MetricType(Enum):
    """Enumeration of supported evaluation metric types."""
    PRECISION_AT_K = "precision_at_k"
    RECALL_AT_K = "recall_at_k"
    DIVERSITY = "diversity"
    COVERAGE = "coverage"
    NDCG = "ndcg"
    MAP = "map"


@dataclass
class EvaluationMetric:
    """
    Represents a calculated evaluation metric for a recommendation set.

    Attributes:
        metric_type: The type of metric (e.g., Precision@K).
        value: The calculated numerical value.
        k: The K parameter for metrics like Precision@K (if applicable).
        seed_id: The seed item ID this metric was calculated for.
        method: The method used to generate the recommendations (e.g., 'greedy', 'beam').
    """
    metric_type: MetricType
    value: float
    k: Optional[int] = None
    seed_id: Optional[str] = None
    method: str = "unknown"

    def __repr__(self) -> str:
        k_str = f"@{self.k}" if self.k else ""
        return f"EvaluationMetric({self.metric_type.value}{k_str}={self.value:.4f}, method={self.method})"