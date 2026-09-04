import os
from pathlib import Path
import random
import numpy as np

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

# Configuration
MAX_TRIALS = 5000
BOOTSTRAP_N_JOBS = 2
RANDOM_SEED = 42

def get_config():
    """Return the configuration dictionary."""
    return {
        "data_dir": str(DATA_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "figures_dir": str(FIGURES_DIR),
        "analysis_dir": str(ANALYSIS_DIR),
        "max_trials": MAX_TRIALS,
        "bootstrap_n_jobs": BOOTSTRAP_N_JOBS,
        "random_seed": RANDOM_SEED
    }

def get_data_dir() -> str:
    """Return the data directory path."""
    return str(DATA_DIR)

def get_processed_dir() -> str:
    """Return the processed directory path."""
    return str(PROCESSED_DIR)

def set_seed(seed: int = RANDOM_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)