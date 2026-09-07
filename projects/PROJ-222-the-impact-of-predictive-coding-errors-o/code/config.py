import os
from pathlib import Path
import random
import numpy as np

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def get_config():
    """
    Get the configuration dictionary for the project.
    """
    return {
        "random_seed": 42,
        "max_trials": 5000,
        "laplace_alpha": 1.0,
        "bootstrap_n_jobs": 2,
        "power_target": 0.8,
        "chunk_size": 10000
    }

def get_data_dir() -> Path:
    """
    Get the data directory path.
    """
    return PROJECT_ROOT / "data"

def get_processed_dir() -> Path:
    """
    Get the processed data directory path.
    """
    return get_data_dir() / "processed"

def get_figures_dir() -> Path:
    """
    Get the figures directory path.
    """
    return PROJECT_ROOT / "figures"

def set_seed(seed: int = 42):
    """
    Set random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(os, 'environ'):
        os.environ['PYTHONHASHSEED'] = str(seed)