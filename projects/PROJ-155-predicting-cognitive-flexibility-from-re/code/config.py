"""
Configuration module – provides a deterministic random seed and a few
pipeline parameters.
"""
import os
import random
from typing import Any

import numpy as np

# Constants required by the task specification
SEED = 42
WINDOW_SEC = 60          # seconds, per spec
STEP_SEC = 1
FD_THRESHOLD = 0.2
BATCH_SIZE = 20

# Internal configuration dictionary (used by other modules)
_CONFIG: dict[str, Any] = {
    "seed": SEED,
    "tr": float(os.getenv("TR", "0.72")),  # HCP repetition time in seconds
    "window_seconds": WINDOW_SEC,
    "step_seconds": STEP_SEC,
    "FD_threshold": FD_THRESHOLD,
    "batch_size": BATCH_SIZE,
    "snr_threshold": 1.0,
}

def set_seed(seed: int = SEED) -> None:
    """
    Seed the global random number generators for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_config() -> dict[str, Any]:
    """
    Return a copy of the current configuration dictionary.
    """
    return dict(_CONFIG)
