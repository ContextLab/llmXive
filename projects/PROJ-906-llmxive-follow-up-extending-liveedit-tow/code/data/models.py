from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import numpy as np

@dataclass
class VideoClip:
    id: str
    path: str
    motion_category: str
    flow_field: Optional[np.ndarray] = None
    mask: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricRecord:
    clip_id: str
    model_variant: str
    peak_memory: float
    fps: float
    ssim: float
    gradient_variance: float
    flow_magnitude: float
    invalid_flow: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AnalysisResult:
    pvalue: float
    regression_coeff: float
    threshold: float
    sensitivity_table: Dict[float, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())