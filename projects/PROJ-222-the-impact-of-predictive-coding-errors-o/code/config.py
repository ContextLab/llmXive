import os
from pathlib import Path

# Constants for convergence handling (T022b)
CONVERGENCE_THRESHOLD = 0.90

def get_config():
    """Return configuration dictionary."""
    return {
        "convergence_threshold": CONVERGENCE_THRESHOLD,
        "random_seed": 42
    }

def get_data_dir():
    """Return the data directory path."""
    return Path("data")

def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    import random
    import numpy as np
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass
    random.seed(seed)
    np.random.seed(seed)
