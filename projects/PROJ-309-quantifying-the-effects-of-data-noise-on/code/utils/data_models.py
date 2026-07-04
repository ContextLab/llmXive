"""
Data models for the quantifying noise effects project.

Defines dataclasses for trajectory data structures used throughout the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
from enum import Enum

class NoiseType(Enum):
    """Enum for supported noise types."""
    GAUSSIAN = "gaussian"
    QUANTIZATION = "quantization"

@dataclass
class Trajectory:
    """Represents a clean trajectory from a dynamical system."""
    system_type: str
    seed: int
    parameters: Dict[str, float]
    time_points: np.ndarray
    state_data: np.ndarray  # Shape: (n_points, n_dimensions)
    
    def validate(self) -> bool:
        """Validate trajectory integrity."""
        if self.state_data is None or self.time_points is None:
            return False
        if len(self.state_data) == 0:
            return False
        if np.any(np.isnan(self.state_data)) or np.any(np.isinf(self.state_data)):
            return False
        if len(self.state_data) != len(self.time_points):
            return False
        return True

@dataclass
class NoisyTrajectory:
    """Represents a trajectory with injected noise."""
    system_type: str
    seed: int
    target_snr_db: float
    actual_snr_db: float
    noise_type: NoiseType
    parameters: Dict[str, float]
    time_points: np.ndarray
    clean_data: np.ndarray
    noisy_data: np.ndarray
    
    def validate(self) -> bool:
        """Validate noisy trajectory integrity."""
        if self.noisy_data is None or self.clean_data is None:
            return False
        if len(self.noisy_data) == 0 or len(self.clean_data) == 0:
            return False
        if np.any(np.isnan(self.noisy_data)) or np.any(np.isinf(self.noisy_data)):
            return False
        if len(self.noisy_data) != len(self.clean_data):
            return False
        return True

@dataclass
class MetricResult:
    """Represents a computed metric for a trajectory."""
    system_type: str
    seed: int
    snr_db: float
    noise_type: NoiseType
    metric_name: str
    computed_value: float
    ground_truth_value: float
    error_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "system_type": self.system_type,
            "seed": self.seed,
            "snr_db": self.snr_db,
            "noise_type": self.noise_type.value,
            "metric_name": self.metric_name,
            "computed_value": self.computed_value,
            "ground_truth_value": self.ground_truth_value,
            "error_percent": self.error_percent
        }
