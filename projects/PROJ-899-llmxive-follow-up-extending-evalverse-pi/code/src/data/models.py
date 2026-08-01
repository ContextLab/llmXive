from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class VideoClip:
    clip_id: str
    file_path: str
    duration: float
    frame_count: int
    resolution: Tuple[int, int]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureVector:
    clip_id: str
    features: np.ndarray
    feature_names: List[str]
    extraction_timestamp: Optional[str] = None

@dataclass
class DimensionScore:
    dimension_name: str
    correlation: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    status: str  # "feature-sufficient" or "VLM-required"
    p_value: Optional[float] = None
