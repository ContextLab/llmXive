import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Constraint from FR-007: Max docs to ensure < 1 hour runtime
MAX_DOCS = 360

# Hyperparameters
WINDOW_SIZE = 10
RANDOM_SEED = 42
MIN_DF = 2
MAX_DF = 0.95
N_TOP_TERMS = 1000
