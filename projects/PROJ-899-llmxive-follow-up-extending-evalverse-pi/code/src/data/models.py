from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class VideoClip:
    path: str
    duration: float
    fps: int
    resolution: Tuple[int, int]

@dataclass
class FeatureVector:
    optical_flow: Optional[np.ndarray] = None
    hog_density: Optional[np.ndarray] = None
    audio_features: Optional[np.ndarray] = None

@dataclass
class DimensionScore:
    dimension: str
    score: float
    confidence_interval: Tuple[float, float]
    status: str # "feature-sufficient" or "VLM-required"
