from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from code.config import NoiseType

@dataclass
class Trajectory:
    """Represents a clean time-series trajectory."""
    data: np.ndarray
    system_type: str
    seed: int
    time_vector: Optional[np.ndarray] = None
    dt: Optional[float] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.data is not None:
            if not isinstance(self.data, np.ndarray):
                self.data = np.array(self.data)
            if np.any(np.isnan(self.data)):
                logging.warning("Trajectory contains NaN values.")
            if len(self.data) < 10:
                logging.warning("Trajectory length is below minimum threshold.")

@dataclass
class NoisyTrajectory:
    """Represents a trajectory with injected noise."""
    data: np.ndarray
    system_type: str
    seed: int
    noise_type: NoiseType
    snr_db: float
    actual_snr_db: float
    quantization_bits: Optional[int] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.data is not None:
            if not isinstance(self.data, np.ndarray):
                self.data = np.array(self.data)

@dataclass
class MetricResult:
    """Stores the result of a metric computation."""
    metric_name: str
    value: float
    error_percent: Optional[float] = None
    ground_truth_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)