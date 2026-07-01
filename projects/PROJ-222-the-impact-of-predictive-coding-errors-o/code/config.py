"""
Configuration management for the project.
Handles random seeds and path definitions.
"""
import os
from pathlib import Path

# Random seed for reproducibility
RANDOM_SEED = 42

def get_config():
    return {
        "random_seed": RANDOM_SEED,
        "data_dir": str(get_data_dir()),
        "code_dir": "code",
        "output_dir": "data/processed",
        "figures_dir": "figures"
    }

def get_data_dir() -> Path:
    """Returns the project data directory."""
    return Path("data")

def set_seed(seed: int):
    global RANDOM_SEED
    RANDOM_SEED = seed
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)