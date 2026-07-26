import os
import random
from typing import Set, List

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Memory Threshold
MAX_RAM_GB = 7

# Alpha Set for Sensitivity Analysis
ALPHA_SET = {0.01, 0.05, 0.1}

# Random Seed
RANDOM_SEED = 42

def set_random_seed(seed: int = RANDOM_SEED):
    random.seed(seed)
    if 'numpy' in globals() or 'numpy' in locals():
        import numpy as np
        np.random.seed(seed)

def get_path(key: str) -> str:
    """Get a specific path based on key."""
    paths = {
        "project_root": PROJECT_ROOT,
        "raw": os.path.join(PROJECT_ROOT, "data", "raw"),
        "interim": os.path.join(PROJECT_ROOT, "data", "interim"),
        "processed": os.path.join(PROJECT_ROOT, "data", "processed"),
    }
    return paths.get(key, "")

def get_alpha_set() -> Set[float]:
    return ALPHA_SET

def get_memory_threshold_mb() -> int:
    return MAX_RAM_GB * 1024
