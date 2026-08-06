import os

# Seed for reproducibility
SEED = 42

# Permutation test parameters
PERMUTATION_COUNT = 1000

# Batch processing parameters
BATCH_SIZE = 50  # Number of queries to process in a single batch

# Memory thresholds (in GB)
MEMORY_THRESHOLD_GB = 6.0
MAX_MEMORY_GB = 7.0

# Runtime thresholds (in seconds)
RUNTIME_SOFT_LIMIT_HOURS = 3.5
RUNTIME_HARD_LIMIT_HOURS = 5.0

# Subsampling parameters
SUBSAMPLE_QUERY_COUNT = 100  # Number of queries to use if subsampling is triggered

# Path configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
NULL_DISTRIBUTIONS_DIR = os.path.join(RESULTS_DIR, "null_distributions")
P_VALUES_DIR = os.path.join(RESULTS_DIR, "p_values")
MDES_DIR = os.path.join(RESULTS_DIR, "mdes")
SENSITIVITY_DIR = os.path.join(RESULTS_DIR, "sensitivity")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")

# Ensure directories exist
def ensure_dirs():
    """Create all required output directories if they do not exist."""
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        RESULTS_DIR,
        NULL_DISTRIBUTIONS_DIR,
        P_VALUES_DIR,
        MDES_DIR,
        SENSITIVITY_DIR,
        PLOTS_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Initialize directories on module import
ensure_dirs()