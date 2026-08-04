"""
Configuration constants and utility functions for the statistical validity evaluation pipeline.
"""
import os
import logging

# --- Paths ---
# Base project directory (assumed to be the parent of 'code')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RESULTS_NULL_DIR = os.path.join(RESULTS_DIR, "null_distributions")
RESULTS_PVALUES_DIR = os.path.join(RESULTS_DIR, "p_values")
RESULTS_MDES_DIR = os.path.join(RESULTS_DIR, "mdes")
RESULTS_SENSITIVITY_DIR = os.path.join(RESULTS_DIR, "sensitivity")
RESULTS_PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")

# --- Hyperparameters ---
SEED = 42
PERMUTATION_COUNT = 1000
BATCH_SIZE = 10  # Queries per batch for memory management
MAX_MEMORY_GB = 6.0
MAX_RUNTIME_HOURS = 5.0
SUBSAMPLE_QUERY_LIMIT = 100

# --- Logging Configuration ---
# Ensure logging is configured to INFO level by default, removing debug prints from code
# and using structured logging instead.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """
    Creates all necessary output directories if they do not exist.
    Uses logging.info for status updates instead of debug prints.
    """
    dirs = [
        DATA_RAW_DIR,
        RESULTS_DIR,
        RESULTS_NULL_DIR,
        RESULTS_PVALUES_DIR,
        RESULTS_MDES_DIR,
        RESULTS_SENSITIVITY_DIR,
        RESULTS_PLOTS_DIR
    ]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            logger.info(f"Created directory: {d}")
        else:
            logger.debug(f"Directory already exists: {d}")
