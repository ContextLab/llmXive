import os
from pathlib import Path
from typing import List, Optional

# Constants
RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"
INTERACTION_SIG_THRESHOLD = 0.05
INCLUDE_INTERACTION = False  # Default False as per task description
DATA_URL = "https://raw.githubusercontent.com/llmXive/datasets/main/addhealth_wave4_sample.csv"

def ensure_directories():
    """Create necessary project directories."""
    dirs = [
        DATA_ROOT,
        os.path.join(DATA_ROOT, "raw"),
        os.path.join(DATA_ROOT, "processed"),
        RESULTS_ROOT,
        os.path.join(RESULTS_ROOT, "models"),
        os.path.join(RESULTS_ROOT, "figures"),
        "logs",
        "contracts",
        "tests"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_data_path(subpath: str) -> str:
    """Get full path for a data file."""
    return os.path.join(DATA_ROOT, subpath)

def get_results_path(subpath: str) -> str:
    """Get full path for a results file."""
    return os.path.join(RESULTS_ROOT, subpath)

def get_logs_path(subpath: str) -> str:
    """Get full path for a log file."""
    return os.path.join("logs", subpath)
