from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
from enum import Enum

class NoiseType(Enum):
    GAUSSIAN = "Gaussian"
    UNIFORM_QUANTIZATION = "Uniform Quantization"

@dataclass
class Trajectory:
    system_type: str
    seed: int
    time: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray

@dataclass
class NoisyTrajectory:
    system_type: str
    seed: int
    time: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    noise_x: np.ndarray
    noise_y: np.ndarray
    noise_z: np.ndarray
    snr_db: float
    noise_type: NoiseType
    checksum: Optional[str] = None

@dataclass
class MetricResult:
    metric_name: str
    value: float
    error_percent: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
