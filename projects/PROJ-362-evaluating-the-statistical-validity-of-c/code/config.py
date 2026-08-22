"""
Configuration constants and utilities for PROJ-362.

This module centralizes all hyperparameters, paths, and thresholds
required for the statistical validity evaluation pipeline.
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
CONFIG_DIR = RESULTS_DIR / "config"

# Constants for Permutation Tests
PERMUTATION_N = 1000
SEED = 42
BATCH_SIZE = 50

# Resource Thresholds (enforced by FR-011 and system constraints)
MEMORY_THRESHOLD_GB = 6.0
RUNTIME_THRESHOLD_HOURS = 5.0

# Alpha Sweep Configuration for Sensitivity Analysis
ALPHA_SWEEP_START = 0.01
ALPHA_SWEEP_END = 0.20
ALPHA_SWEEP_STEP = 0.01

# Data Sources (placeholders for real paths, set via env or config file)
TREC_ROBUST_DATASET_ID = "trec-robust-2004"
TREC_WEB_DATASET_ID = "trec-web-2009"
NIST_ARCHIVE_PATH = os.getenv("NIST_ARCHIVE_PATH", None)

# Path Constants for Output Artifacts (used by T007 and downstream tasks)
DATA_RAW_PATH = RAW_DATA_DIR
RESULTS_PATH = RESULTS_DIR

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
        SENSITIVITY_DIR,
        CONFIG_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs