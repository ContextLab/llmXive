from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class MaskedRegion:
    image_id: str
    mask_path: str
    mask_complexity_score: float
    gradient_variance: float
    texture_entropy: float
    mask_coverage: float

@dataclass
class InferenceResult:
    image_id: str
    predicted_rank: int
    inference_time_ms: float
    reconstruction_loss: float
    fid_score: float
    lpps_score: float

@dataclass
class GatingState:
    complexity_input: float
    predicted_rank: int
    rank_modulation_factor: float
    fallback_triggered: bool = False
