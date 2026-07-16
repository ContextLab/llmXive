import os
import random
from typing import Set, List

# Project root directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Random seed for reproducibility
_RANDOM_SEED = 42

# Significance thresholds for sensitivity analysis
_ALPHA_SET: Set[float] = {0.01, 0.05, 0.1}

# Memory threshold in MB (approx 7GB for safety margin)
_MEMORY_THRESHOLD_MB = 7000

def set_random_seed(seed: int = _RANDOM_SEED) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_path(*subdirs: str, filename: str = "") -> str:
    """
    Construct an absolute path relative to the project root.
    
    Args:
        *subdirs: Subdirectories to traverse
        filename: Optional filename at the end
    
    Returns:
        Absolute path string
    """
    parts = [_PROJECT_ROOT] + list(subdirs)
    if filename:
        parts.append(filename)
    return os.path.join(*parts)

def get_alpha_set() -> Set[float]:
    """Return the set of alpha thresholds for sensitivity analysis."""
    return _ALPHA_SET

def get_memory_threshold_mb() -> int:
    """Return the memory threshold in MB."""
    return _MEMORY_THRESHOLD_MB
