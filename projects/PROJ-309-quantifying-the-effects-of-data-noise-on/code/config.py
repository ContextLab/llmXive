import numpy as np
from scipy.stats import t, norm
from enum import Enum
from typing import List, Dict, Any, Tuple

class NoiseType(Enum):
    GAUSSIAN = "Gaussian"
    UNIFORM_QUANTIZATION = "Uniform Quantization"

def get_snr_levels() -> List[float]:
    """Return list of SNR levels in dB."""
    return [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

def get_seeds() -> List[int]:
    """Return list of random seeds."""
    return [42, 123]

def get_system_params() -> Dict[str, Dict[str, float]]:
    """Return parameters for Lorenz and Rössler systems."""
    return {
        "lorenz": {"sigma": 10.0, "rho": 28.0, "beta": 8.0/3.0},
        "rossler": {"a": 0.2, "b": 0.2, "c": 5.7}
    }

def get_noise_types() -> List[NoiseType]:
    """Return list of supported noise types."""
    return [NoiseType.GAUSSIAN, NoiseType.UNIFORM_QUANTIZATION]

def get_literature_bounds() -> Dict[str, Tuple[float, float]]:
    """Return literature bounds for metrics."""
    return {
        "correlation_dimension": (1.5, 2.5),
        "lyapunov_exponent": (0.6, 0.9)
    }
