import os
from pathlib import Path
import random
import numpy as np

def get_config():
    return {
        "seed": 42,
        "max_trials": None,
        "bootstrap_n_jobs": min(2, os.cpu_count())
    }

def get_data_dir():
    """Returns the path to the data directory."""
    return Path(__file__).parent.parent / "data"

def get_processed_dir():
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def set_seed(seed: int = 42):
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)