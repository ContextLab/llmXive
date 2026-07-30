import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).resolve().parent
CODE_DIR = ROOT_DIR / "code"
DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_FEATURES_DIR = DATA_DIR / "features"
FIGURES_DIR = ROOT_DIR / "figures"
STATE_DIR = ROOT_DIR / "state"
STATE_PROJECTS_DIR = STATE_DIR / "projects"
TESTS_DIR = ROOT_DIR / "tests"
SPECS_DIR = ROOT_DIR / "specs"

# Constants
RANDOM_SEED = 42
TOLERANCE_WEIGHT_FRACTION = 0.02
MAX_RAM_CAPACITY_GB = 14.0  # Default max RAM for sampling decisions

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "pipeline.log"

# Model Hyperparameters (Defaults)
N_ESTIMATORS = 100
MAX_DEPTH = 10

# VIF Thresholds
VIF_WARNING_THRESHOLD = 5.0
VIF_CRITICAL_THRESHOLD = 10.0

# Data Gates
MIN_DATASET_SIZE = 100
JOIN_FAILURE_RATE_THRESHOLD = 0.50
JOIN_FAILURE_RATE_CRITICAL = 0.50