"""
Configuration module for the quantifying noise effects project.

Contains constants, enums, and configuration functions for:
- SNR levels
- System parameters (Lorenz, Rössler)
- Random seeds
- Noise types
"""
import numpy as np
from scipy.stats import t, norm
from enum import Enum
from typing import List, Dict, Any, Tuple

class NoiseType(Enum):
    """Enum for supported noise types."""
    GAUSSIAN = "gaussian"
    QUANTIZATION = "quantization"

# System parameters
LORENZ_PARAMS = {
    "sigma": 10.0,
    "rho": 28.0,
    "beta": 8.0/3.0,
    "dt": 0.01,
    "t_max": 100.0,
    "initial_state": [1.0, 1.0, 1.0]
}

ROSSLER_PARAMS = {
    "a": 0.2,
    "b": 0.2,
    "c": 5.7,
    "dt": 0.01,
    "t_max": 100.0,
    "initial_state": [1.0, 1.0, 1.0]
}

# SNR levels (in dB)
DEFAULT_SNR_LEVELS = [0, 5, 10, 15, 20, 25, 30]

# Random seeds for reproducibility
DEFAULT_SEEDS = [42, 123, 456]

# Noise types available
DEFAULT_NOISE_TYPES = [NoiseType.GAUSSIAN, NoiseType.QUANTIZATION]

def get_snr_levels() -> List[float]:
    """Get the list of SNR levels to test."""
    return DEFAULT_SNR_LEVELS.copy()

def get_seeds() -> List[int]:
    """Get the list of random seeds for reproducibility."""
    return DEFAULT_SEEDS.copy()

def get_system_params(system_type: str) -> Dict[str, Any]:
    """Get system parameters for a given system type."""
    if system_type == "lorenz":
        return LORENZ_PARAMS.copy()
    elif system_type == "rossler":
        return ROSSLER_PARAMS.copy()
    else:
        raise ValueError(f"Unknown system type: {system_type}")

def get_noise_types() -> List[NoiseType]:
    """Get the list of available noise types."""
    return DEFAULT_NOISE_TYPES.copy()

def get_literature_bounds(metric_name: str) -> Tuple[float, float]:
    """
    Get literature bounds for a given metric.
    
    Args:
        metric_name: Name of the metric (e.g., "correlation_dimension", "lyapunov_exponent")
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    bounds = {
        "correlation_dimension_lorenz": (1.9, 2.1),
        "correlation_dimension_rossler": (2.0, 2.2),
        "lyapunov_exponent_lorenz": (0.8, 0.9),
        "lyapunov_exponent_rossler": (0.07, 0.09)
    }
    
    key = f"{metric_name}_{system_type}" if "correlation" in metric_name or "lyapunov" in metric_name else metric_name
    if key in bounds:
        return bounds[key]
    else:
        # Default wide bounds if not found
        return (-np.inf, np.inf)

# Additional configuration for analysis thresholds
FNN_THRESHOLD_MULTIPLIER = 10.0  # FNN threshold = multiplier * std
MIN_TRAJECTORY_LENGTH = 1000  # Minimum number of points for valid analysis
EMBEDDING_DIM_RANGE = range(1, 11)  # Range of embedding dimensions to test