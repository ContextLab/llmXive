"""
Configuration module for the statistical validity evaluation project.

Contains constants for seeds, permutation counts, batch sizes, and memory thresholds.
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data paths
DATA_RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_PATH = os.path.join(PROJECT_ROOT, "data", "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
RESULTS_NULL_DISTRIBUTIONS = os.path.join(RESULTS_DIR, "null_distributions")
RESULTS_P_VALUES = os.path.join(RESULTS_DIR, "p_values")
RESULTS_MDES = os.path.join(RESULTS_DIR, "mdes")
RESULTS_SENSITIVITY = os.path.join(RESULTS_DIR, "sensitivity")
RESULTS_PLOTS = os.path.join(RESULTS_DIR, "plots")

# Permutation test constants
PERMUTATION_N = 1000
SEED = 42
BATCH_SIZE = 50

# Resource constraints
MEMORY_THRESHOLD_GB = 6.0
RUNTIME_THRESHOLD_HOURS = 3.5

# MDES calculation constants
MDES_EFFECT_SIZE_RANGE = (0.001, 0.500)
MDES_TOLERANCE = 0.001
MDES_MIN_POWER = 0.8

# Benjamini-Hochberg correction
BH_ALPHA = 0.05

def ensure_dirs(path: Path) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
