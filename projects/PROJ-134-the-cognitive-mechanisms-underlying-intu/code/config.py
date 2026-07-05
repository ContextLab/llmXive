import os
from pathlib import Path
import random
import numpy as np

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths
DIRS = {
    "code": "code",
    "data": "data",
    "tests": "tests",
    "state": "state",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_logs": "data/logs",
    "reports": "reports",
    "figures": "figures"
}

# Random seed for reproducibility
RANDOM_SEED = 42

def ensure_directories():
    """Create all required directories if they don't exist."""
    for dir_name in DIRS.values():
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def init_random_seeds(seed: int = RANDOM_SEED):
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed