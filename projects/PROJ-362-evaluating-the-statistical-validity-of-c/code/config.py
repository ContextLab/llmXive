"""
Configuration constants and utilities for PROJ-362.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "plots"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Directories for specific outputs
NULL_DISTRIBUTIONS_DIR = RESULTS_DIR / "null_distributions"
P_VALUES_DIR = RESULTS_DIR / "p_values"
MDES_DIR = RESULTS_DIR / "mdes"
SENSITIVITY_DIR = RESULTS_DIR / "sensitivity"

# Constants for Permutation Tests
PERMUTATION_N = 1000
SEED = 42
BATCH_SIZE = 50
MEMORY_THRESHOLD_GB = 6.0
RUNTIME_THRESHOLD_HOURS = 3.5

# Data Sources (placeholders for real paths, set via env or config file)
TREC_ROBUST_DATASET_ID = "trec-robust-2004"
TREC_WEB_DATASET_ID = "trec-web-2009"
NIST_ARCHIVE_PATH = os.getenv("NIST_ARCHIVE_PATH", None)

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        NULL_DISTRIBUTIONS_DIR,
        P_VALUES_DIR,
        MDES_DIR,
        SENSITIVITY_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs
