"""
Core data structures for the topic drift analysis pipeline.

This module defines the fundamental entities used throughout the pipeline:
- AbstractRecord: Represents a single academic abstract with metadata
- TopicVector: Represents the topic distribution for a document or window
- DivergenceMeasurement: Represents the statistical divergence between two topic distributions
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AbstractRecord:
    """
    Represents a single academic abstract with its metadata and processed tokens.

    Attributes:
        id: Unique identifier for the record (e.g., arXiv ID or PubMed ID)
        title: Title of the paper
        abstract: Full text of the abstract
        year: Publication year
        source: Source of the abstract ('arxiv' or 'pubmed')
        categories: List of subject categories (for arXiv) or MeSH terms (for PubMed)
        tokens: List of preprocessed tokens after stopword removal
        window: The 5-year time window this record belongs to
        raw_metadata: Dictionary containing any additional raw metadata
    """
    id: str
    title: str
    abstract: str
    year: int
    source: str
    tokens: List[str] = field(default_factory=list)
    window: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the record after initialization."""
        if not self.id:
            raise ValueError("AbstractRecord ID cannot be empty")
        if not self.title:
            raise ValueError("AbstractRecord title cannot be empty")
        if not self.abstract:
            raise ValueError("AbstractRecord abstract cannot be empty")
        if self.year < 1900 or self.year > 2025:
            raise ValueError(f"AbstractRecord year {self.year} is out of reasonable range")
        if self.source not in ['arxiv', 'pubmed']:
            logger.warning(f"Unexpected source '{self.source}' for record {self.id}")

    @property
    def token_count(self) -> int:
        """Return the number of tokens in this record."""
        return len(self.tokens)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'year': self.year,
            'source': self.source,
            'tokens': self.tokens,
            'window': self.window,
            'categories': self.categories,
            'raw_metadata': self.raw_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractRecord':
        """Create an AbstractRecord from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            abstract=data['abstract'],
            year=data['year'],
            source=data['source'],
            tokens=data.get('tokens', []),
            window=data.get('window'),
            categories=data.get('categories', []),
            raw_metadata=data.get('raw_metadata', {})
        )


@dataclass
class TopicVector:
    """
    Represents a topic distribution vector for a document or time window.

    This class encapsulates the probability distribution over topics,
    ensuring that the vector is valid (sums to 1.0, no NaN values).

    Attributes:
        window: The time window this vector represents (e.g., '2000-2004')
        topic_probs: Numpy array of topic probabilities (shape: [n_topics])
        topic_ids: Optional list of topic identifiers for reference
        model_params: Dictionary of LDA model parameters used to generate this vector
    """
    window: str
    topic_probs: np.ndarray = field(default_factory=lambda: np.array([]))
    topic_ids: Optional[List[str]] = None
    model_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize the topic vector after initialization."""
        if self.topic_probs is None:
            self.topic_probs = np.array([])
        
        # Convert to numpy array if it isn't already
        self.topic_probs = np.array(self.topic_probs, dtype=np.float64)
        
        # Validate dimensions
        if self.topic_probs.ndim != 1:
            raise ValueError(f"TopicVector must be 1D, got {self.topic_probs.ndim}D")
        
        # Check for NaN values
        if np.any(np.isnan(self.topic_probs)):
            raise ValueError("TopicVector contains NaN values")
        
        # Normalize to sum to 1.0 if not already
        total = np.sum(self.topic_probs)
        if total == 0:
            logger.warning(f"TopicVector for window {self.window} has zero sum, setting to uniform")
            n_topics = len(self.topic_probs)
            if n_topics > 0:
                self.topic_probs = np.ones(n_topics) / n_topics
        else:
            self.topic_probs = self.topic_probs / total

    @property
    def n_topics(self) -> int:
        """Return the number of topics in this vector."""
        return len(self.topic_probs)

    @property
    def is_valid(self) -> bool:
        """Check if the topic vector is valid (sums to 1.0, no NaN)."""
        return (
            np.sum(np.abs(np.sum(self.topic_probs) - 1.0)) < 1e-6 and
            not np.any(np.isnan(self.topic_probs)) and
            not np.any(np.isinf(self.topic_probs))
        )

    def get_top_k_topics(self, k: int = 5) -> List[Tuple[int, float]]:
        """
        Return the indices and probabilities of the top k topics.

        Args:
            k: Number of top topics to return

        Returns:
            List of (topic_index, probability) tuples sorted by probability descending
        """
        if k <= 0:
            return []
        
        sorted_indices = np.argsort(self.topic_probs)[::-1]
        return [(int(idx), float(self.topic_probs[idx])) for idx in sorted_indices[:k]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the topic vector to a dictionary for serialization."""
        return {
            'window': self.window,
            'topic_probs': self.topic_probs.tolist(),
            'topic_ids': self.topic_ids,
            'model_params': self.model_params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicVector':
        """Create a TopicVector from a dictionary."""
        return cls(
            window=data['window'],
            topic_probs=np.array(data['topic_probs'], dtype=np.float64),
            topic_ids=data.get('topic_ids'),
            model_params=data.get('model_params', {})
        )


@dataclass
class DivergenceMeasurement:
    """
    Represents a statistical divergence measurement between two topic distributions.

    This class encapsulates the Jensen-Shannon divergence (or other metrics)
    between two TopicVectors, along with statistical test results.

    Attributes:
        window_pair: Tuple of (window_a, window_b) being compared
        divergence_value: The computed divergence value (e.g., JS divergence)
        p_value: P-value from permutation test (if performed)
        confidence_interval: 95% confidence interval as (lower, upper) tuple
        is_significant: Whether the divergence is statistically significant
        permutation_count: Number of permutations used in the test
        correction_method: Method used for multiple comparison correction (e.g., 'maxT')
        raw_stats: Dictionary of additional raw statistics from the computation
    """
    window_pair: Tuple[str, str]
    divergence_value: float = 0.0
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    is_significant: bool = False
    permutation_count: int = 0
    correction_method: Optional[str] = None
    raw_stats: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the measurement after initialization."""
        if len(self.window_pair) != 2:
            raise ValueError("window_pair must be a tuple of exactly two window names")
        
        if self.window_pair[0] == self.window_pair[1]:
            raise ValueError("Cannot compute divergence between identical windows")
        
        # Ensure divergence value is non-negative
        if self.divergence_value < 0:
            logger.warning(f"Negative divergence value {self.divergence_value} for {self.window_pair}")
            self.divergence_value = 0.0

    @property
    def is_valid(self) -> bool:
        """Check if the measurement is valid."""
        return (
            self.divergence_value >= 0 and
            (self.p_value is None or (0 <= self.p_value <= 1)) and
            (self.confidence_interval is None or 
             (len(self.confidence_interval) == 2 and 
              self.confidence_interval[0] <= self.confidence_interval[1]))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the measurement to a dictionary for serialization."""
        return {
            'window_pair': list(self.window_pair),
            'divergence_value': float(self.divergence_value),
            'p_value': self.p_value,
            'confidence_interval': list(self.confidence_interval) if self.confidence_interval else None,
            'is_significant': self.is_significant,
            'permutation_count': self.permutation_count,
            'correction_method': self.correction_method,
            'raw_stats': self.raw_stats
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DivergenceMeasurement':
        """Create a DivergenceMeasurement from a dictionary."""
        return cls(
            window_pair=tuple(data['window_pair']),
            divergence_value=float(data['divergence_value']),
            p_value=data.get('p_value'),
            confidence_interval=tuple(data['confidence_interval']) if data.get('confidence_interval') else None,
            is_significant=data.get('is_significant', False),
            permutation_count=data.get('permutation_count', 0),
            correction_method=data.get('correction_method'),
            raw_stats=data.get('raw_stats', {})
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        significance = "significant" if self.is_significant else "not significant"
        return (
            f"DivergenceMeasurement({self.window_pair[0]} vs {self.window_pair[1]}): "
            f"JS={self.divergence_value:.4f}, p={self.p_value:.4f} ({significance})"
        )
