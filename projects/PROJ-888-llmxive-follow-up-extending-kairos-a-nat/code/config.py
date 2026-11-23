import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
import numpy as np

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Configuration constants
QUANTIZATION_LEVELS: List[int] = [4, 6, 8, 16]
NOISE_STD_DEVS: List[float] = [0.0, 0.1, 0.2]

# Dataset settings
SUBSET_SIZE: int = 50

# Power analysis defaults
POWER_EFFECT_SIZE: float = 0.5
POWER_TARGET: float = 0.8
POWER_ALPHA: float = 0.05
POWER_ICC: float = 0.3
POWER_TIMEPOINTS: int = 100

def ensure_dirs():
    """Create all required directories if they don't exist."""
    dirs = [
        DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR,
        RESULTS_DIR, LOGS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of current configuration."""
    return {
        "quantization_levels": QUANTIZATION_LEVELS,
        "noise_std_devs": NOISE_STD_DEVS,
        "subset_size": SUBSET_SIZE,
        "power_effect_size": POWER_EFFECT_SIZE,
        "power_target": POWER_TARGET,
        "power_alpha": POWER_ALPHA,
        "power_icc": POWER_ICC,
        "power_timepoints": POWER_TIMEPOINTS
    }
