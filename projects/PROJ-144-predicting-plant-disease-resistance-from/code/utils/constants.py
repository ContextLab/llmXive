import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"
RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"

# Random seeds
RANDOM_SEED = 42

# Hypothesis thresholds
BALANCED_ACC_THRESHOLD = 0.75

# Data splitting
HOLD_OUT_FRACTION = 0.20

# Model Grid Search
MAX_DEPTH_GRID = [5, 10, 15]

# Permutation testing
N_PERMUTATIONS = 1000

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        CODE_DIR, DATA_DIR, TESTS_DIR, STATE_DIR, RESULTS_DIR, CONTRACTS_DIR,
        DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR, RESULTS_PLOTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
