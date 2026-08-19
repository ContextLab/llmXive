"""
Central configuration for the Narrative Archaeology project.

This module defines:
- Pinned random seeds for reproducibility
- CPU-only constraints (no CUDA)
- Project path definitions
- Analysis parameters (motion thresholds, etc.)
"""

import os
import random
from pathlib import Path

# ============================================================================
# Random Seeds (Pinned for Reproducibility)
# ============================================================================
RANDOM_SEED = 42
os.environ["PYTHONHASHSEED"] = str(RANDOM_SEED)

# Set seeds for numpy and torch (if available)
try:
    import numpy as np
    np.random.seed(RANDOM_SEED)
except ImportError:
    pass

try:
    import torch
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        # Force CPU-only as per constraints
        torch.set_num_threads(2)
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
except ImportError:
    pass

# ============================================================================
# Project Paths
# ============================================================================
# Determine project root relative to this file (code/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

ROOT_DIR = _PROJECT_ROOT
CODE_DIR = ROOT_DIR / "code"
DATA_DIR = ROOT_DIR / "data"
TESTS_DIR = ROOT_DIR / "tests"
SPECS_DIR = ROOT_DIR / "specs"
FIGURES_DIR = ROOT_DIR / "figures"
LOGS_DIR = ROOT_DIR / "logs"

# Ensure directories exist (optional, but good for initialization)
# Note: In a real execution environment, these might be created by the runner.
# We do not enforce creation here to avoid side-effects in pure config loading.

# ============================================================================
# Execution Constraints (CPU-Only)
# ============================================================================
# Enforce CPU-only usage to comply with CI/CD free-tier limits
USE_CUDA = False
N_CPUS = 2  # Match GitHub Actions free-tier vCPU limits

# ============================================================================
# Analysis Parameters
# ============================================================================
# Motion artifact threshold (in mm)
# Subjects exceeding this displacement will be skipped
MOTION_THRESHOLD_MM = 3.0

# HRF convolution parameters
HRF_FWHM = 6.0  # Full Width at Half Maximum in seconds

# RSA parameters
RSA_METRIC = "correlation"  # Options: "correlation", "euclidean"

# Decoder parameters
DECODER_C = 1.0  # Regularization strength for RidgeClassifier

# Statistical testing parameters
PERMUTATION_ITERATIONS = 1000
FDR_ALPHA = 0.05

# OpenNeuro Dataset ID
DATASET_ID = "ds000234"

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "pipeline.log"
ERROR_LOG_FILE = DATA_DIR / "errors.log"

# ============================================================================
# Data Paths (Relative to project root)
# ============================================================================
RAW_DATA_DIR = DATA_DIR / "raw"
PREPROCESSED_DATA_DIR = DATA_DIR / "preprocessed"
EVENT_ANNOTATIONS_FILE = DATA_DIR / "event_annotations.csv"
ROI_MASKS_DIR = DATA_DIR / "roi_masks"

# ============================================================================
# Model Paths
# ============================================================================
MODEL_OUTPUT_DIR = DATA_DIR / "models"
RESULTS_DIR = DATA_DIR / "results"

# ============================================================================
# Verification Helpers
# ============================================================================
def get_data_path(filename: str) -> Path:
    """Return the full path for a file in the data directory."""
    return DATA_DIR / filename

def get_output_path(filename: str) -> Path:
    """Return the full path for a file in the results directory."""
    return RESULTS_DIR / filename

def get_figure_path(filename: str) -> Path:
    """Return the full path for a file in the figures directory."""
    return FIGURES_DIR / filename
