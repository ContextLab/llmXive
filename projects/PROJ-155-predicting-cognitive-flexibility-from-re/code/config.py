"""
Configuration module – provides a deterministic random seed and a few
pipeline parameters.
"""

import os
import random
from typing import Dict, Any

import numpy as np


_CONFIG: Dict[str, Any] = {
    # Reproducibility
    "seed": int(os.getenv("SEED", "42")),
    # fMRI acquisition parameters
    "tr": 0.72,  # HCP repetition time in seconds
    "window_seconds": 60,
    "step_seconds": 1,
    # Miscellaneous
    "snr_threshold": 1.0,
    "batch_size": 50,
}


def set_seed(seed: int = 42) -> None:
    """
    Seed the global random number generators for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_config() -> Dict[str, Any]:
    """
    Return a copy of the current configuration dictionary.
    """
    return dict(_CONFIG)