from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AbstractRecord:
    """
    Represents a single academic abstract record.
    
    Attributes:
        id: Unique identifier for the abstract (e.g., arXiv ID or PubMed ID)
        title: Title of the paper
        text: Full text content of the abstract (preprocessed)
        source: Source of the abstract ('arxiv' or 'pubmed')
        year: Publication year
        window: 5-year window label (e.g., '2000-2004')
        tokens: List of tokenized words (optional, for debugging)
        metadata: Additional metadata dictionary
    """
    id: str
    title: str
    text: str
    source: str
    year: int
    window: str
    tokens: Optional[List[str]] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        if not self.id:
            raise ValueError("AbstractRecord requires a non-empty id")
        if not self.text:
            raise ValueError("AbstractRecord requires non-empty text")
        if self.source not in ['arxiv', 'pubmed']:
            raise ValueError(f"AbstractRecord source must be 'arxiv' or 'pubmed', got '{self.source}'")
        if not (2000 <= self.year <= 2024):
            raise ValueError(f"AbstractRecord year must be between 2000 and 2024, got {self.year}")

    def to_dict(self) -> Dict[str, any]:
        """Convert record to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'source': self.source,
            'year': self.year,
            'window': self.window,
            'tokens': self.tokens,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'AbstractRecord':
        """Create an AbstractRecord from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            text=data['text'],
            source=data['source'],
            year=data['year'],
            window=data['window'],
            tokens=data.get('tokens', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class TopicVector:
    """
    Represents a topic distribution vector for a specific window.
    
    Attributes:
        window: The 5-year window this vector represents
        topic_proportions: Numpy array of topic proportions (sum to 1.0)
        topic_words: List of top words for each topic (list of lists)
        topic_weights: Optional weights for topics (e.g., from LDA model)
        k: Number of topics
        coherence_score: Optional coherence score for validation
    """
    window: str
    topic_proportions: np.ndarray
    topic_words: List[List[str]]
    topic_weights: Optional[np.ndarray] = None
    k: int = 10
    coherence_score: Optional[float] = None

    def __post_init__(self):
        """Validate and normalize the topic vector."""
        if not isinstance(self.topic_proportions, np.ndarray):
            self.topic_proportions = np.array(self.topic_proportions)
        
        if self.topic_proportions.ndim != 1:
            raise ValueError(f"topic_proportions must be 1D array, got {self.topic_proportions.ndim}D")
        
        if len(self.topic_proportions) != self.k:
            raise ValueError(f"topic_proportions length ({len(self.topic_proportions)}) must match k ({self.k})")
        
        # Ensure proportions sum to 1.0 (with floating point tolerance)
        total = np.sum(self.topic_proportions)
        if not np.isclose(total, 1.0, atol=1e-6):
            # Normalize if close to 1.0
            if total > 0:
                self.topic_proportions = self.topic_proportions / total
            else:
                raise ValueError("topic_proportions sum to zero, cannot normalize")
        
        if len(self.topic_words) != self.k:
            raise ValueError(f"topic_words length ({len(self.topic_words)}) must match k ({self.k})")

    def to_dict(self) -> Dict[str, any]:
        """Convert topic vector to dictionary for serialization."""
        return {
            'window': self.window,
            'topic_proportions': self.topic_proportions.tolist(),
            'topic_words': self.topic_words,
            'topic_weights': self.topic_weights.tolist() if self.topic_weights is not None else None,
            'k': self.k,
            'coherence_score': self.coherence_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'TopicVector':
        """Create a TopicVector from a dictionary."""
        return cls(
            window=data['window'],
            topic_proportions=np.array(data['topic_proportions']),
            topic_words=data['topic_words'],
            topic_weights=np.array(data['topic_weights']) if data.get('topic_weights') is not None else None,
            k=data['k'],
            coherence_score=data.get('coherence_score')
        )

    def get_topic_probability(self, topic_idx: int) -> float:
        """Get the probability of a specific topic."""
        if 0 <= topic_idx < self.k:
            return float(self.topic_proportions[topic_idx])
        raise IndexError(f"Topic index {topic_idx} out of range [0, {self.k})")


@dataclass
class DivergenceMeasurement:
    """
    Represents a Jensen-Shannon divergence measurement between two topic vectors.
    
    Attributes:
        window_1: First window label
        window_2: Second window label
        js_divergence: The JS divergence value (base 2)
        js_distance: The JS distance (square root of divergence)
        p_value: Optional p-value from permutation test
        confidence_interval: Optional 95% confidence interval tuple (lower, upper)
        corrected_p_value: Optional p-value after MaxT correction
        significant: Whether the divergence is statistically significant
    """
    window_1: str
    window_2: str
    js_divergence: float
    js_distance: float
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    corrected_p_value: Optional[float] = None
    significant: bool = False

    def __post_init__(self):
        """Validate the divergence measurement."""
        if not (0.0 <= self.js_divergence <= 1.0):
            raise ValueError(f"JS divergence must be in [0, 1], got {self.js_divergence}")
        
        if not (0.0 <= self.js_distance <= 1.0):
            raise ValueError(f"JS distance must be in [0, 1], got {self.js_distance}")
        
        if self.p_value is not None and not (0.0 <= self.p_value <= 1.0):
            raise ValueError(f"p-value must be in [0, 1], got {self.p_value}")

    def to_dict(self) -> Dict[str, any]:
        """Convert divergence measurement to dictionary for serialization."""
        return {
            'window_1': self.window_1,
            'window_2': self.window_2,
            'js_divergence': self.js_divergence,
            'js_distance': self.js_distance,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'corrected_p_value': self.corrected_p_value,
            'significant': self.significant
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'DivergenceMeasurement':
        """Create a DivergenceMeasurement from a dictionary."""
        return cls(
            window_1=data['window_1'],
            window_2=data['window_2'],
            js_divergence=data['js_divergence'],
            js_distance=data['js_distance'],
            p_value=data.get('p_value'),
            confidence_interval=tuple(data['confidence_interval']) if data.get('confidence_interval') else None,
            corrected_p_value=data.get('corrected_p_value'),
            significant=data.get('significant', False)
        )

    def is_significant_at_alpha(self, alpha: float = 0.05) -> bool:
        """Check if the measurement is significant at the given alpha level."""
        if self.p_value is None:
            return False
        p = self.corrected_p_value if self.corrected_p_value is not None else self.p_value
        return p < alpha