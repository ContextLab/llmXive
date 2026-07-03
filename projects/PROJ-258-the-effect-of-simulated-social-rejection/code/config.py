"""
Configuration management for the project.
Handles paths, random seeds, and alpha thresholds.
"""
import os
import random
from typing import Set, List

# Random Seed for reproducibility
RANDOM_SEED = 42

# Alpha thresholds for statistical testing
ALPHA_THRESHOLDS: Set[float] = {0.01, 0.05, 0.1}

# Project Root (assumed to be the directory containing this file's parent)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory Structure Paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_INTERIM_DIR = os.path.join(DATA_DIR, "interin")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

def set_random_seed(seed: int = RANDOM_SEED) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_path(relative_path: str) -> str:
    """Returns the absolute path for a given relative path from project root."""
    return os.path.join(PROJECT_ROOT, relative_path)
