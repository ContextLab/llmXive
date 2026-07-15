import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DIR_CODE = PROJECT_ROOT / "code"
DIR_TESTS = PROJECT_ROOT / "tests"
DIR_DATA_RAW = PROJECT_ROOT / "data" / "raw"
DIR_DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DIR_DATA_LOGS = PROJECT_ROOT / "data" / "logs"
DIR_RESULTS = PROJECT_ROOT / "results"
DIR_STATE = PROJECT_ROOT / "state"
DIR_FIGURES = PROJECT_ROOT / "figures"

# Seed
RANDOM_SEED = 42

# Constants
DEFAULT_DENSITY_THRESHOLD = 0.1
MOTIF_SIZE = 3
MAX_TIMEOUT_SECONDS = 100

def ensure_dirs():
    """Create all required directories if they don't exist."""
    dirs = [
        DIR_CODE,
        DIR_TESTS,
        DIR_DATA_RAW,
        DIR_DATA_PROCESSED,
        DIR_DATA_LOGS,
        DIR_RESULTS,
        DIR_STATE,
        DIR_FIGURES
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
