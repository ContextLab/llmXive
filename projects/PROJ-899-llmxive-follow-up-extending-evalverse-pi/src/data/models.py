"""
Data models for the llmXive project.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class VideoClip:
    """Represents a video clip with its metadata and features."""
    id: str
    path: str
    duration: float
    fps: float
    resolution: Tuple[int, int]
    has_audio: bool = True
    features: Optional[Dict[str, np.ndarray]] = None
    expert_scores: Optional[Dict[str, float]] = None

@dataclass
class FeatureVector:
    """Represents a feature vector extracted from a video clip."""
    clip_id: str
    features: Dict[str, float]
    timestamp: Optional[float] = None

@dataclass
class DimensionScore:
    """Represents a score for a specific technical dimension."""
    dimension: str
    score: float
    confidence_interval: Optional[Tuple[float, float]] = None
    status: Optional[str] = None  # "feature-sufficient", "VLM-required", etc.
