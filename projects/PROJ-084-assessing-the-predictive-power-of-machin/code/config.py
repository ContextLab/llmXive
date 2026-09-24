import os
from pathlib import Path
from typing import Dict, List, Any

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_PATH = DATA_DIR / "raw"
DATA_PROCESSED_PATH = DATA_DIR / "processed"
DATA_RESULTS_PATH = DATA_DIR / "results"

# Configuration for yield parsing
# Options: 'midpoint', 'exclude'
# Default: 'exclude' if not set
YIELD_RANGE_STRATEGY = os.getenv("YIELD_RANGE_STRATEGY", "exclude")

# Random seeds
RANDOM_SEED = 42

# Hyperparameter grids (examples)
RF_GRID = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None]
}

SVM_GRID = {
    'C': [0.1, 1.0, 10.0],
    'kernel': ['linear', 'rbf']
}

def ensure_dirs():
    """Create required directories if they don't exist."""
    dirs = [
        DATA_RAW_PATH,
        DATA_PROCESSED_PATH,
        DATA_RESULTS_PATH,
        CODE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_dirs()
