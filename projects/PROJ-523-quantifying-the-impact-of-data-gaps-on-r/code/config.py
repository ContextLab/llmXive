"""
Global configuration constants for the CMB Gap Bias Analysis project.

This module defines paths, seeds, and global parameters used across the pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"

# Data Directories
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DERIVED_DIR = DATA_DIR / "derived"
DATA_METADATA_DIR = DATA_DIR / "metadata"
DATA_RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"

# Ensure directories exist
def ensure_directories():
    """Create all necessary data directories if they don't exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_DERIVED_DIR,
        DATA_METADATA_DIR,
        DATA_RESULTS_DIR,
        FIGURES_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Simulation Parameters
N_SIDE = 512
RANDOM_SEED = 42
FORCE_FLOAT32 = True

def get_dtype():
    """Return the appropriate numpy dtype based on FORCE_FLOAT32 setting."""
    return np.float32 if FORCE_FLOAT32 else np.float64

# Gap Configuration
GAP_FRACTIONS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
GAP_MORPHOLOGIES = ["random", "clustered", "point_source", "galactic_plane", "null_model"]

# Analysis Parameters
MAX_L = 2000
L_MIN = 2
BUDGET_TIME_SEC = 3600  # 1 hour budget for pilot/runs

# Initialize directories on import
ensure_directories()

# Ensure numpy is imported for get_dtype
import numpy as np