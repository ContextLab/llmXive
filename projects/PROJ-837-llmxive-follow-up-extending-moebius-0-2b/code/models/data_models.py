from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

@dataclass
class MaskedRegion:
    """Represents a masked region in an image."""
    image_id: str
    mask_path: str
    complexity_score: float
    metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class InferenceResult:
    """Result of an inference run."""
    image_id: str
    latency_ms: float
    fidelity_score: float
    rank_used: int
    metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class GatingState:
    """State of the gating mechanism."""
    complexity_input: float
    predicted_rank: int
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
