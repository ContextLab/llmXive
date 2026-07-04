"""
Configuration constants and enums for the project.

Defines:
- SNR levels
- System parameters (Lorenz, Rössler)
- Seeds
- Noise type enums
- Algorithm parameters (FNN_THRESHOLD_FACTOR, etc.)
"""
import numpy as np
from scipy.stats import t, norm
from enum import Enum
from typing import List, Dict, Any, Optional


class NoiseType(Enum):
    """Enumeration of supported noise types."""
    GAUSSIAN = "gaussian"
    UNIFORM_QUANTIZATION = "uniform_quantization"


# System Parameters
LORENZ_PARAMS = {
    'sigma': 10.0,
    'rho': 28.0,
    'beta': 8.0/3.0
}

ROSSLER_PARAMS = {
    'a': 0.2,
    'b': 0.2,
    'c': 5.7
}

# Integration Parameters
DT = 0.01
T_MAX = 100.0
SAVE_FREQ = 10  # Save every 10 time steps

# Noise Parameters
SNR_LEVELS = [0, 5, 10, 15, 20, 25, 30]  # dB
QUANTIZATION_BITS = [8, 10, 12, 14, 16]

# Algorithm Parameters
FNN_THRESHOLD_FACTOR = 10.0  # Threshold for FNN is 10 * std
FNN_EMBEDDING_START = 1
FNN_EMBEDDING_MAX = 10
FNN_DELAY = 1

# Random Seeds
BASE_SEED = 42
SEEDS = [42, 123, 456, 789, 101112]

# Metric Parameters
CORRELATION_DIM_R_MIN = 0.01
CORRELATION_DIM_R_MAX = 1.0
CORRELATION_DIM_N_BINS = 20

LYAPUNOV_T_MAX = 100
LYAPUNOV_MIN_SEPARATION = 10