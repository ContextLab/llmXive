"""
Configuration module for the motif-rsfc project.
Defines paths, seeds, and constants used throughout the pipeline.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = DATA_DIR / "logs"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Random seed for reproducibility
RANDOM_SEED = 42

# Performance constraints
MOTIF_TIMEOUT_SECONDS = 300  # SC-002: Max 300s per subject

# Statistical parameters
BONFERRONI_ALPHA = 0.05
PERMUTATION_COUNT = 1000
VIF_THRESHOLD = 5.0

def ensure_dirs():
    """Create all necessary directories if they don't exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        RESULTS_DIR,
        STATE_DIR,
        LOGS_DIR,
        PROCESSED_DIR,
        RAW_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    print("Directories ensured.")
