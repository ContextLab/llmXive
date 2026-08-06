import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DIRS = {
    "code": PROJECT_ROOT / "code",
    "tests": PROJECT_ROOT / "tests",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_logs": PROJECT_ROOT / "data" / "logs",
    "results": PROJECT_ROOT / "results",
    "state": PROJECT_ROOT / "state",
}

# Constants
SEED = 42
DEFAULT_DENSITY_THRESHOLDS = [0.1, 0.2, 0.3]

def ensure_dirs():
    """Creates all required project directories if they don't exist."""
    for dir_path in DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    return DIRS
