import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory Structure
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"

# Data Sub-directories
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"

# Results Sub-directories
RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"

# Ensure directories exist
def ensure_dirs():
    dirs = [
        CODE_DIR, DATA_DIR, TESTS_DIR, STATE_DIR, RESULTS_DIR,
        DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR,
        RESULTS_PLOTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_STATE = 42

# Hypothesis Thresholds
BALANCED_ACC_THRESHOLD = 0.75

# Hold-out Fraction
HOLD_OUT_FRACTION = 0.20

# Grid Search Parameters
MAX_DEPTH_GRID = [5, 10, 15, 20]

# Permutation Testing
N_PERMUTATIONS = 1000
