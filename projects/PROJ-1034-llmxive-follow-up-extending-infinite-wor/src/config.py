"""
Global configuration and deterministic seed management.
"""
import os
import random
import numpy as np

# Default seed
DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

# Initialize with default
set_seed()
