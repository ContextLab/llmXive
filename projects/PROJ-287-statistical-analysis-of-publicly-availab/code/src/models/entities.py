"""
Core data structures for the Topic Drift Analysis pipeline.

This module defines the fundamental data entities used throughout the analysis:
- AbstractRecord: Represents a single academic abstract with metadata.
- TopicVector: Represents a probability distribution over topics for a window.
- DivergenceMeasurement: Represents the statistical divergence between two TopicVectors.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AbstractRecord:
    """
    Represents a single academic abstract record.

    Attributes:
        id: Unique identifier for the abstract (e.g., arXiv ID or PubMed ID).
        source: Data source ('arxiv' or 'pubmed').
        title: Title of the paper.
        abstract: The raw text content of the abstract.
        year: Publication year (integer).
        window: The 5-year analysis window this record belongs to (e.g., '2000-2004').
        tokens: List of processed tokens (lowercased, stopwords removed).
        metadata: Additional metadata dictionary (optional).
    """
    id: str
    source: str
    title: str
    abstract: str
    year: int
    window: str
    tokens: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields and types."""
        if not self.id:
            raise ValueError("AbstractRecord requires a non-empty 'id'.")
        if self.source not in ('arxiv', 'pubmed'):
            raise ValueError(f"AbstractRecord 'source' must be 'arxiv' or 'pubmed', got '{self.source}'.")
        if not isinstance(self.year, int) or not (2000 <= self.year <= 2024):
            raise ValueError(f"AbstractRecord 'year' must be an integer between 2000 and 2024, got {self.year}.")
        if not self.window:
            raise ValueError("AbstractRecord requires a non-empty 'window'.")


@dataclass
class TopicVector:
    """
    Represents a topic distribution vector for a specific time window.

    This vector holds the probability mass for each of the k topics,
    ensuring the values sum to 1.0 (valid probability distribution).

    Attributes:
        window: The time window this vector represents (e.g., '2000-2004').
        topic_ids: List of topic identifiers (0 to k-1).
        probabilities: Numpy array of probabilities corresponding to topic_ids.
        model_params: Dictionary of parameters used to generate this vector (e.g., seed, k).
    """
    window: str
    topic_ids: List[int]
    probabilities: np.ndarray
    model_params: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the topic vector structure and probability constraints."""
        if len(self.topic_ids) != len(self.probabilities):
            raise ValueError(
                f"TopicVector: 'topic_ids' length ({len(self.topic_ids)}) must match "
                f"'probabilities' length ({len(self.probabilities)})."
            )

        # Ensure probabilities are a numpy array
        if not isinstance(self.probabilities, np.ndarray):
            self.probabilities = np.array(self.probabilities, dtype=np.float64)
        else:
            self.probabilities = self.probabilities.astype(np.float64)

        # Check for NaN or Inf
        if np.any(np.isnan(self.probabilities)) or np.any(np.isinf(self.probabilities)):
            raise ValueError("TopicVector: Probabilities cannot contain NaN or Inf values.")

        # Check non-negativity
        if np.any(self.probabilities < 0):
            raise ValueError("TopicVector: Probabilities cannot be negative.")

        # Check sum to 1.0 (with tolerance for floating point errors)
        total_mass = np.sum(self.probabilities)
        if not np.isclose(total_mass, 1.0, atol=1e-6):
            raise ValueError(
                f"TopicVector: Probabilities must sum to 1.0 (got {total_mass:.6f}). "
                "Ensure the vector is normalized."
            )

    def get_topic_probability(self, topic_id: int) -> float:
        """
        Retrieve the probability for a specific topic ID.

        Args:
            topic_id: The ID of the topic.

        Returns:
            The probability associated with the topic_id.

        Raises:
            KeyError: If topic_id is not in the vector.
        """
        try:
            idx = self.topic_ids.index(topic_id)
            return float(self.probabilities[idx])
        except ValueError:
            raise KeyError(f"Topic ID {topic_id} not found in vector for window {self.window}.")

    def to_dict(self) -> Dict:
        """Convert the TopicVector to a JSON-serializable dictionary."""
        return {
            "window": self.window,
            "topic_ids": self.topic_ids,
            "probabilities": self.probabilities.tolist(),
            "model_params": self.model_params
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TopicVector':
        """Construct a TopicVector from a dictionary."""
        return cls(
            window=data["window"],
            topic_ids=data["topic_ids"],
            probabilities=np.array(data["probabilities"]),
            model_params=data.get("model_params", {})
        )


@dataclass
class DivergenceMeasurement:
    """
    Represents a statistical divergence measurement between two TopicVectors.

    Attributes:
        window_1: The first time window (source).
        window_2: The second time window (target).
        divergence_value: The calculated divergence value (e.g., Jensen-Shannon).
        divergence_type: The type of metric used (e.g., 'JS_Divergence').
        is_significant: Boolean indicating if the divergence is statistically significant.
        p_value: P-value from the permutation test (optional).
        confidence_interval: Tuple (lower, upper) for the 95% CI (optional).
        metadata: Additional context (e.g., correction method used).
    """
    window_1: str
    window_2: str
    divergence_value: float
    divergence_type: str
    is_significant: Optional[bool] = None
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the measurement."""
        if self.window_1 == self.window_2:
            raise ValueError("DivergenceMeasurement: window_1 and window_2 must be different.")
        if self.divergence_value < 0:
            raise ValueError("DivergenceMeasurement: Divergence value cannot be negative.")

    def to_dict(self) -> Dict:
        """Convert the DivergenceMeasurement to a JSON-serializable dictionary."""
        result = {
            "window_1": self.window_1,
            "window_2": self.window_2,
            "divergence_value": self.divergence_value,
            "divergence_type": self.divergence_type,
            "is_significant": self.is_significant,
            "p_value": self.p_value,
            "confidence_interval": list(self.confidence_interval) if self.confidence_interval else None,
            "metadata": self.metadata
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'DivergenceMeasurement':
        """Construct a DivergenceMeasurement from a dictionary."""
        ci = data.get("confidence_interval")
        if ci and isinstance(ci, list):
            ci = tuple(ci)
        
        return cls(
            window_1=data["window_1"],
            window_2=data["window_2"],
            divergence_value=data["divergence_value"],
            divergence_type=data["divergence_type"],
            is_significant=data.get("is_significant"),
            p_value=data.get("p_value"),
            confidence_interval=ci,
            metadata=data.get("metadata", {})
        )
