import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directory Paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Ensure directories exist
def ensure_dirs():
    """Creates all required project directories if they do not exist."""
    dirs = [
        CODE_DIR, DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR,
        TESTS_DIR, STATE_DIR, RESULTS_DIR, RESULTS_PLOTS_DIR, CONTRACTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_STATE = 42

# Hypothesis Thresholds
BALANCED_ACC_THRESHOLD = 0.75
HOLD_OUT_FRACTION = 0.20
MAX_DEPTH_GRID = [5, 10, 15]

# Initialize directories on import
ensure_dirs()
