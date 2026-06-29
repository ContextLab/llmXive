"""
Configuration management for the neural correlates study.
Handles random seeds, logging paths, and tool configurations.
"""
import os
import yaml
import random
import numpy as np
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Random Seed Configuration
RANDOM_SEED = 42

# Logging Configuration
LOG_DIR = PROJECT_ROOT / "logs"
LOG_PREPROCESSING = LOG_DIR / "preprocessing.log"
LOG_ANALYSIS = LOG_DIR / "analysis.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_config():
    """
    Load and return project configuration.
    Returns a dictionary with random seed, log paths, and directory paths.
    """
    return {
        "random_seed": RANDOM_SEED,
        "log_paths": {
            "preprocessing": str(LOG_PREPROCESSING),
            "analysis": str(LOG_ANALYSIS)
        },
        "paths": {
            "data_raw": str(PROJECT_ROOT / "data" / "raw"),
            "data_processed": str(PROJECT_ROOT / "data" / "processed"),
            "code": str(PROJECT_ROOT / "code")
        }
    }

def set_random_seed(seed=None):
    """
    Set the random seed for reproducibility across the entire pipeline.
    If seed is None, uses the default RANDOM_SEED (42).
    Applies seed to:
      - Python's random module
      - NumPy random generator
      - The module's internal RANDOM_SEED constant
    
    Args:
        seed (int, optional): The seed value. Defaults to 42.
    
    Returns:
        int: The seed value that was set.
    """
    global RANDOM_SEED
    if seed is None:
        seed = RANDOM_SEED
    
    # Ensure seed is an integer
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed).__name__}")
    
    # Set seed for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    RANDOM_SEED = seed
    
    return RANDOM_SEED