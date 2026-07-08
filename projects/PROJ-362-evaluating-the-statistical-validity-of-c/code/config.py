import os

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory Paths
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "plots")
MDES_DIR = os.path.join(RESULTS_DIR, "mdes")
SENSITIVITY_DIR = os.path.join(RESULTS_DIR, "sensitivity")
NULL_DIST_DIR = os.path.join(RESULTS_DIR, "null_distributions")
P_VALUES_DIR = os.path.join(RESULTS_DIR, "p_values")

# Constants
SEED = 42
PERMUTATION_COUNT = 1000
LOG_LEVEL = "INFO"

def ensure_dirs():
    """Create necessary directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        MDES_DIR,
        SENSITIVITY_DIR,
        NULL_DIST_DIR,
        P_VALUES_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
