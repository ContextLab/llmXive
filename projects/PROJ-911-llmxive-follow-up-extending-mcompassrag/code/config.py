import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Hyperparameters
WINDOW_SIZE = 10
MAX_DOCS = 360
RANDOM_SEED = 42

# Retrieval parameters
RECALL_K = 10

# Ensure directories exist
def setup_directories():
    """Create data directories if they don't exist."""
    for dir_path in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
setup_directories()
