"""
Base data structures for the Topic Drift Analysis pipeline.

This module defines the core data entities used throughout the research:
- AbstractRecord: Represents a single academic abstract with metadata.
- TopicVector: Represents the distribution of topics for a document or window.
- DivergenceMeasurement: Represents the statistical divergence between two topic vectors.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AbstractRecord:
    """
    Represents a single academic abstract record.

    Attributes:
        id: Unique identifier for the record (e.g., arXiv ID or PubMed ID).
        title: Title of the academic paper.
        abstract: The text content of the abstract.
        source: The source database (e.g., 'arxiv', 'pubmed').
        year: Publication year.
        categories: List of subject categories/keywords.
        tokens: Preprocessed list of tokens (optional, populated after preprocessing).
    """
    id: str
    title: str
    abstract: str
    source: str
    year: int
    categories: List[str] = field(default_factory=list)
    tokens: Optional[List[str]] = None

    def __post_init__(self):
        """Validate the record upon initialization."""
        if not isinstance(self.year, int) or self.year < 1900 or self.year > 2099:
            raise ValueError(f"Invalid year: {self.year}. Must be between 1900 and 2099.")
        if not self.abstract or not self.abstract.strip():
            raise ValueError("Abstract text cannot be empty.")
        if not self.id:
            raise ValueError("Record ID cannot be empty.")

    def to_dict(self) -> Dict:
        """Convert the record to a dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "abstract": self.abstract,
            "source": self.source,
            "year": self.year,
            "categories": self.categories,
            "tokens": self.tokens
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AbstractRecord":
        """Create an AbstractRecord from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            abstract=data["abstract"],
            source=data["source"],
            year=data["year"],
            categories=data.get("categories", []),
            tokens=data.get("tokens")
        )


@dataclass
class TopicVector:
    """
    Represents a topic distribution vector.

    This can represent the topic proportions of a single document or an aggregate
    topic distribution for a time window.

    Attributes:
        window_label: Identifier for the time window (e.g., "2000-2004") or document ID.
        vector: Numpy array of topic probabilities (must sum to 1.0).
        topic_indices: Optional list of topic indices if the vector is sparse.
        model_id: Identifier for the LDA model that generated this vector.
    """
    window_label: str
    vector: np.ndarray
    model_id: Optional[str] = None
    topic_indices: Optional[List[int]] = None

    def __post_init__(self):
        """Validate and normalize the vector."""
        if not isinstance(self.vector, np.ndarray):
            self.vector = np.array(self.vector, dtype=np.float64)
        
        # Ensure non-negative
        if np.any(self.vector < 0):
            raise ValueError("Topic probabilities cannot be negative.")
        
        # Normalize to sum to 1.0 if not already
        total = np.sum(self.vector)
        if total == 0:
            raise ValueError("Topic vector cannot be all zeros.")
        
        if not np.isclose(total, 1.0, atol=1e-6):
            self.vector = self.vector / total

    @property
    def k(self) -> int:
        """Return the number of topics (dimension of the vector)."""
        return len(self.vector)

    def get_topic_probability(self, topic_idx: int) -> float:
        """Get the probability of a specific topic."""
        if topic_idx < 0 or topic_idx >= self.k:
            raise IndexError(f"Topic index {topic_idx} out of range [0, {self.k})")
        return float(self.vector[topic_idx])

    def to_dict(self) -> Dict:
        """Convert the vector to a dictionary for JSON serialization."""
        return {
            "window_label": self.window_label,
            "vector": self.vector.tolist(),
            "model_id": self.model_id,
            "topic_indices": self.topic_indices,
            "k": self.k
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TopicVector":
        """Create a TopicVector from a dictionary."""
        return cls(
            window_label=data["window_label"],
            vector=np.array(data["vector"], dtype=np.float64),
            model_id=data.get("model_id"),
            topic_indices=data.get("topic_indices")
        )


@dataclass
class DivergenceMeasurement:
    """
    Represents a statistical divergence measurement between two topic vectors.

    Attributes:
        window_pair: Tuple of (window_a, window_b) labels being compared.
        divergence_type: Type of divergence (e.g., 'JS', 'KL').
        value: The calculated divergence value.
        p_value: P-value from permutation test (optional).
        confidence_interval: Tuple (lower, upper) for the 95% CI (optional).
        is_significant: Boolean indicating if the result is statistically significant.
        method_details: Dictionary of additional parameters used in calculation.
    """
    window_pair: Tuple[str, str]
    divergence_type: str
    value: float
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    is_significant: Optional[bool] = None
    method_details: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate the measurement."""
        if len(self.window_pair) != 2:
            raise ValueError("window_pair must be a tuple of exactly two window labels.")
        if self.value < 0:
            raise ValueError(f"Divergence value cannot be negative: {self.value}")
        
        # Validate CI if present
        if self.confidence_interval is not None:
            if not isinstance(self.confidence_interval, tuple) or len(self.confidence_interval) != 2:
                raise ValueError("confidence_interval must be a tuple of (lower, upper).")
            if self.confidence_interval[0] > self.confidence_interval[1]:
                raise ValueError("CI lower bound cannot be greater than upper bound.")

    def to_dict(self) -> Dict:
        """Convert the measurement to a dictionary."""
        return {
            "window_pair": list(self.window_pair),
            "divergence_type": self.divergence_type,
            "value": float(self.value),
            "p_value": self.p_value,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            "is_significant": self.is_significant,
            "method_details": self.method_details
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DivergenceMeasurement":
        """Create a DivergenceMeasurement from a dictionary."""
        return cls(
            window_pair=tuple(data["window_pair"]),
            divergence_type=data["divergence_type"],
            value=data["value"],
            p_value=data.get("p_value"),
            confidence_interval=tuple(data["confidence_interval"]) if data.get("confidence_interval") else None,
            is_significant=data.get("is_significant"),
            method_details=data.get("method_details", {})
        )