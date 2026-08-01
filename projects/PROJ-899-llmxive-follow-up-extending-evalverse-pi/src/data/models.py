"""
Data models for the llmXive project.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class VideoClip:
    """Represents a video clip with its metadata."""
    clip_id: str
    file_path: str
    duration: float
    width: int
    height: int
    fps: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureVector:
    """Represents a feature vector extracted from a video clip."""
    clip_id: str
    features: np.ndarray
    feature_names: List[str]
    extraction_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DimensionScore:
    """Represents a score for a technical dimension."""
    dimension: str
    score: float
    confidence_interval: Optional[Tuple[float, float]] = None
    classification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
