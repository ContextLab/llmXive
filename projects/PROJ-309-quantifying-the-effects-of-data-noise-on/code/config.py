import numpy as np
from scipy.stats import t, norm
from enum import Enum
from typing import List, Dict, Any, Tuple

class NoiseType(Enum):
    """Enumeration of supported noise types."""
    GAUSSIAN = "gaussian"
    QUANTIZATION = "quantization"

def get_snr_levels() -> List[float]:
    """Returns list of SNR levels in dB to test."""
    return [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

def get_seeds() -> List[int]:
    """Returns list of random seeds for reproducibility testing."""
    return [42, 123, 456, 789, 101112]

def get_system_params(system_name: str) -> Dict[str, float]:
    """Returns default system parameters for the specified system."""
    if system_name == 'lorenz':
        return {'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0}
    elif system_name == 'rossler':
        return {'a': 0.2, 'b': 0.2, 'c': 5.7}
    else:
        raise ValueError(f"Unknown system: {system_name}")

def get_noise_types() -> List[NoiseType]:
    """Returns list of supported noise types."""
    return [NoiseType.GAUSSIAN, NoiseType.QUANTIZATION]

def get_literature_bounds(metric_name: str) -> Tuple[float, float]:
    """Returns expected literature bounds for a metric."""
    if metric_name == 'correlation_dimension':
        # Lorenz D2 ~ 2.05, Rössler D2 ~ 2.0
        return (1.8, 2.3)
    elif metric_name == 'lyapunov_exponent':
        # Lorenz lambda1 ~ 0.9, Rössler lambda1 ~ 0.07
        return (0.05, 1.0)
    else:
        return (0.0, float('inf'))
