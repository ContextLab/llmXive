from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from src.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AbstractRecord:
    """
    Represents a single academic abstract with metadata.
    
    Attributes:
        id: Unique identifier for the abstract (e.g., arXiv ID or PubMed ID)
        title: Title of the paper
        text: Preprocessed text content (tokenized or raw)
        year: Publication year
        source: Data source ('arxiv' or 'pubmed')
        window: Time window assignment (e.g., '2000-2004')
        original_text: Raw text before preprocessing (optional, for audit)
        tokens: List of tokens after preprocessing (optional)
        metadata: Additional metadata dictionary
    """
    id: str
    title: str
    text: str
    year: int
    source: str
    window: str
    original_text: Optional[str] = None
    tokens: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate that required fields are present and non-empty."""
        if not self.id or not isinstance(self.id, str):
            logger.error(f"Invalid abstract ID: {self.id}")
            return False
        if not self.title or not isinstance(self.title, str):
            logger.error(f"Invalid title for abstract {self.id}")
            return False
        if not self.text or not isinstance(self.text, str):
            logger.error(f"Invalid text for abstract {self.id}")
            return False
        if not isinstance(self.year, int) or self.year < 1900 or self.year > 2100:
            logger.error(f"Invalid year {self.year} for abstract {self.id}")
            return False
        if self.source not in ['arxiv', 'pubmed']:
            logger.error(f"Invalid source {self.source} for abstract {self.id}")
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'year': self.year,
            'source': self.source,
            'window': self.window,
            'original_text': self.original_text,
            'tokens': self.tokens,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractRecord':
        """Create AbstractRecord from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            text=data['text'],
            year=data['year'],
            source=data['source'],
            window=data['window'],
            original_text=data.get('original_text'),
            tokens=data.get('tokens'),
            metadata=data.get('metadata', {})
        )

@dataclass
class TopicVector:
    """
    Represents a topic distribution vector for a time window or document.
    
    Attributes:
        window: Time window identifier (e.g., '2000-2004')
        topic_proportions: Numpy array of topic proportions (sums to 1.0)
        topic_words: List of top words per topic (list of lists)
        k_topics: Number of topics
        model_params: Dictionary of LDA model parameters used
        coherence_score: CV coherence score for the model
        alignment_map: Optional mapping from topic indices to aligned indices
    """
    window: str
    topic_proportions: np.ndarray
    topic_words: List[List[str]]
    k_topics: int
    model_params: Dict[str, Any] = field(default_factory=dict)
    coherence_score: Optional[float] = None
    alignment_map: Optional[Dict[int, int]] = None

    def __post_init__(self):
        """Validate and normalize topic proportions."""
        if not isinstance(self.topic_proportions, np.ndarray):
            self.topic_proportions = np.array(self.topic_proportions)
        
        if self.topic_proportions.ndim != 1:
            raise ValueError(f"topic_proportions must be 1D, got {self.topic_proportions.ndim}D")
        
        if self.k_topics <= 0:
            raise ValueError(f"k_topics must be positive, got {self.k_topics}")
        
        if len(self.topic_proportions) != self.k_topics:
            raise ValueError(f"topic_proportions length {len(self.topic_proportions)} != k_topics {self.k_topics}")
        
        # Normalize to ensure sum = 1.0
        total = np.sum(self.topic_proportions)
        if total > 0:
            self.topic_proportions = self.topic_proportions / total
        else:
            logger.warning(f"Zero topic proportions for window {self.window}, setting uniform distribution")
            self.topic_proportions = np.ones(self.k_topics) / self.k_topics

    def validate(self) -> bool:
        """Validate the topic vector."""
        if np.any(np.isnan(self.topic_proportions)):
            logger.error(f"NaN in topic proportions for window {self.window}")
            return False
        
        if np.any(self.topic_proportions < 0):
            logger.error(f"Negative values in topic proportions for window {self.window}")
            return False
        
        if not np.isclose(np.sum(self.topic_proportions), 1.0, atol=1e-6):
            logger.error(f"Topic proportions for window {self.window} do not sum to 1.0: {np.sum(self.topic_proportions)}")
            return False
        
        return True

    def get_aligned_topic(self, original_idx: int) -> int:
        """Get the aligned topic index for a given original index."""
        if self.alignment_map is None:
            return original_idx
        return self.alignment_map.get(original_idx, original_idx)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'window': self.window,
            'topic_proportions': self.topic_proportions.tolist(),
            'topic_words': self.topic_words,
            'k_topics': self.k_topics,
            'model_params': self.model_params,
            'coherence_score': self.coherence_score,
            'alignment_map': self.alignment_map
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicVector':
        """Create TopicVector from dictionary."""
        return cls(
            window=data['window'],
            topic_proportions=np.array(data['topic_proportions']),
            topic_words=data['topic_words'],
            k_topics=data['k_topics'],
            model_params=data.get('model_params', {}),
            coherence_score=data.get('coherence_score'),
            alignment_map=data.get('alignment_map')
        )

@dataclass
class DivergenceMeasurement:
    """
    Represents a Jensen-Shannon divergence measurement between two topic vectors.
    
    Attributes:
        window_pair: Tuple of (window1, window2) being compared
        divergence_value: JS divergence value (base 2)
        p_value: P-value from permutation test (optional)
        is_significant: Whether the divergence is statistically significant
        confidence_interval: 95% CI as (lower, upper) tuple (optional)
        permutation_count: Number of permutations used (optional)
        max_t_statistic: MaxT statistic if correction was applied (optional)
        adjusted_p_value: P-value after MaxT correction (optional)
    """
    window_pair: Tuple[str, str]
    divergence_value: float
    p_value: Optional[float] = None
    is_significant: bool = False
    confidence_interval: Optional[Tuple[float, float]] = None
    permutation_count: Optional[int] = None
    max_t_statistic: Optional[float] = None
    adjusted_p_value: Optional[float] = None

    def __post_init__(self):
        """Validate the divergence measurement."""
        if len(self.window_pair) != 2:
            raise ValueError(f"window_pair must be a tuple of 2 windows, got {self.window_pair}")
        
        if self.window_pair[0] >= self.window_pair[1]:
            logger.warning(f"Window pair {self.window_pair} is not ordered, sorting...")
            self.window_pair = tuple(sorted(self.window_pair))
        
        if self.divergence_value < 0 or self.divergence_value > 1.0:
            logger.warning(f"Divergence value {self.divergence_value} outside [0, 1] range")

    def validate(self) -> bool:
        """Validate the measurement."""
        if np.isnan(self.divergence_value):
            logger.error(f"NaN divergence value for window pair {self.window_pair}")
            return False
        
        if self.p_value is not None and (self.p_value < 0 or self.p_value > 1.0):
            logger.error(f"Invalid p-value {self.p_value} for window pair {self.window_pair}")
            return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'window_pair': list(self.window_pair),
            'divergence_value': self.divergence_value,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'confidence_interval': self.confidence_interval,
            'permutation_count': self.permutation_count,
            'max_t_statistic': self.max_t_statistic,
            'adjusted_p_value': self.adjusted_p_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DivergenceMeasurement':
        """Create DivergenceMeasurement from dictionary."""
        return cls(
            window_pair=tuple(data['window_pair']),
            divergence_value=data['divergence_value'],
            p_value=data.get('p_value'),
            is_significant=data.get('is_significant', False),
            confidence_interval=tuple(data['confidence_interval']) if data.get('confidence_interval') else None,
            permutation_count=data.get('permutation_count'),
            max_t_statistic=data.get('max_t_statistic'),
            adjusted_p_value=data.get('adjusted_p_value')
        )
