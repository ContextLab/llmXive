import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"
STATE_DIR = PROJECT_ROOT / "state"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_dirs():
    dirs = [
        DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR,
        RESULTS_DIR, RESULTS_PLOTS_DIR, STATE_DIR, TESTS_DIR, SPECS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Constants for modeling
RANDOM_STATE = 42
HOLD_OUT_FRACTION = 0.20
MAX_DEPTH_GRID = [5, 10, 15, 20, None]
N_PERMUTATIONS = 1000
N_ESTIMATORS = 500
MIN_SAMPLES_FOR_HOLDOUT = 50
BALANCED_ACC_THRESHOLD = 0.75
