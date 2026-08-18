"""
Configuration constants for the statistical validity evaluation pipeline.
"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
NULL_DISTRIBUTIONS_DIR = RESULTS_DIR / "null_distributions"
P_VALUES_DIR = RESULTS_DIR / "p_values"
MDES_DIR = RESULTS_DIR / "mdes"
SENSITIVITY_DIR = RESULTS_DIR / "sensitivity"
PLOTS_DIR = RESULTS_DIR / "plots"

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        RESULTS_DIR,
        NULL_DISTRIBUTIONS_DIR,
        P_VALUES_DIR,
        MDES_DIR,
        SENSITIVITY_DIR,
        PLOTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Permutation Test Configuration
SEED = 42
PERMUTATION_COUNT = 1000
BATCH_SIZE = 50  # Number of queries to process in a batch

# Memory & Runtime Constraints
MEMORY_THRESHOLD_GB = 6.0
RUNTIME_LIMIT_HOURS = 5.0
RUNTIME_WARNING_HOURS = 3.5
SUBSAMPLE_QUERY_COUNT = 100

# Dataset Configuration
DATASET_NAME = "trec-robust-2004" # Placeholder, actual name might vary based on loader
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5
