import os
from pathlib import Path

# Project Configuration Constants
# Defined per FR-001 and plan.md specifications

# Target upper bound for prime generation
N_MAX = 10**10

# Default window size for sliding window analysis
WINDOW_SIZE = 10**6

# Step size for sliding window (1 for full overlap)
WINDOW_STEP = 1

# Global deterministic seed for reproducibility (Constitution Principle III)
# This seed is used to initialize all random number generators in the pipeline
GLOBAL_SEED = 42

# File system paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"
SPEC_DIR = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_directories():
    """Create all required project directories if they do not exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        STATE_DIR,
        SPEC_DIR,
        PROJECT_ROOT / "figures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_global_seed():
    """Return the global deterministic seed constant."""
    return GLOBAL_SEED

# Initialize directories on module import to satisfy T001 requirements
ensure_directories()
