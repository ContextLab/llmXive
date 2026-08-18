import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Random seed
DEFAULT_SEED = 42

# Convergence threshold (SC-002)
CONVERGENCE_THRESHOLD = 0.90

def get_config():
    """Return configuration dictionary."""
    return {
        "data_dir": str(DATA_DIR),
        "analysis_dir": str(ANALYSIS_DIR),
        "figures_dir": str(FIGURES_DIR),
        "seed": DEFAULT_SEED,
        "convergence_threshold": CONVERGENCE_THRESHOLD
    }

def get_data_dir():
    """Return the data directory path."""
    return DATA_DIR

def set_seed(seed: int = DEFAULT_SEED):
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