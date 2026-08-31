"""
Configuration constants for the project.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
RESULTS_PATH = PROJECT_ROOT / "results"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
FIGURES_PATH = PROJECT_ROOT / "figures"

# Ensure directories exist
def ensure_dirs():
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "config").mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "null_distributions").mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "p_values").mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "mdes").mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "sensitivity").mkdir(parents=True, exist_ok=True)
    (RESULTS_PATH / "plots").mkdir(parents=True, exist_ok=True)

ensure_dirs()

# Permutation settings
PERMUTATION_N = 1000
SEED = 42
BATCH_SIZE = 50

# Resource limits
MEMORY_THRESHOLD_GB = 6.0
RUNTIME_THRESHOLD_HOURS = 5.0

# Alpha sweep for sensitivity analysis
ALPHA_SWEEP_START = 0.01
ALPHA_SWEEP_END = 0.20
ALPHA_SWEEP_STEP = 0.01

# Metrics
METRIC_K = 10

# Logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Initialize logging
import logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
