from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
from enum import Enum

class NoiseType(Enum):
    GAUSSIAN = "gaussian"
    QUANTIZATION = "quantization"

@dataclass
class Trajectory:
    """Represents a clean trajectory from a dynamical system."""
    system_type: str
    seed: int
    t: np.ndarray
    state: np.ndarray
    params: Dict[str, float]

@dataclass
class NoisyTrajectory:
    """Represents a trajectory with injected noise."""
    system_type: str
    seed: int
    noise_type: NoiseType
    snr_db: float
    t: np.ndarray
    state: np.ndarray
    clean_state: np.ndarray
    params: Dict[str, float]

@dataclass
class MetricResult:
    """Represents a computed metric result."""
    metric_name: str
    value: float
    uncertainty: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None
