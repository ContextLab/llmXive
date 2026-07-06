"""
Configuration module for the llmXive Dream Recall Frequency project.

This module initializes default values for seeds, paths, and analysis constants.
It explicitly includes the `deviation_flag` to track the Schaefer-100 vs Schaefer-400
deviation documented in docs/deviation_log.md and docs/requirement_change_record_Schaefer100.md.
"""

import os
from pathlib import Path

# Project Root
# Assumes this file is at code/utils/config.py, so root is 3 levels up
_current_file = Path(__file__).resolve()
PROJECT_ROOT = _current_file.parent.parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
METRICS_DIR = DATA_DIR / "metrics"
ATLAS_DIR = DATA_DIR / "atlas"

RESULTS_DIR = PROJECT_ROOT / "results"
PLOTS_DIR = RESULTS_DIR / "plots"

CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure directories exist (lazy initialization check, not creation to avoid side effects)
# The main pipeline should ensure these exist, but we define the paths here.

# Random Seeds
RANDOM_SEED = 42
NUMPY_SEED = 42
TORCH_SEED = 42  # If torch is ever used, though constraints say CPU only

# Analysis Constants
WINDOW_SIZE = 30  # seconds (TR dependent, assumed TR=1s or scaled appropriately in processing)
STEP_SIZE = 10    # seconds (sliding window step)

# Atlas Configuration
# Per Plan and RCR (T005b), we use Schaefer-100 for statistical validity (rank-deficiency avoidance)
# instead of the Spec's Schaefer-400.
ATLAS_NAME = "Schaefer100"
ATLAS_RESOLUTION = 100

# Deviation Flag
# Explicitly initialized as True to track the deviation from Spec (Schaefer-400) to Plan (Schaefer-100)
# This flag is referenced in T005 (Spec Deviation Log).
DEVIATION_FLAG = True

# Memory Constraints
MAX_MEMORY_GB = 7.0
MAX_MEMORY_BYTES = MAX_MEMORY_GB * 1024**3

# Runtime Constraints
MAX_RUNTIME_SECONDS = 4 * 3600  # 4 hours

# Data Source Constants
OPENNEURO_DATASET_ID = "ds000228"

# ICA-AROMA Flags
ICA_AROMA_FLAGS = {
    "afni": True,
    "reports": False,
    "denoise": "nonaggr"
}

# Thresholds
FD_THRESHOLD_MM = 0.5
MIN_SUBJECTS_N = 50

# Statistical Constants
PERMUTATION_ITERATIONS = 1000
FDR_METHOD = "fdr_bh"  # Benjamini-Hochberg

def get_config_summary():
    """Returns a dictionary of key configuration values for logging."""
    return {
        "atlas": ATLAS_NAME,
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "deviation_flag": DEVIATION_FLAG,
        "max_memory_gb": MAX_MEMORY_GB,
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "min_subjects": MIN_SUBJECTS_N,
        "fd_threshold_mm": FD_THRESHOLD_MM,
        "permutation_iterations": PERMUTATION_ITERATIONS
    }