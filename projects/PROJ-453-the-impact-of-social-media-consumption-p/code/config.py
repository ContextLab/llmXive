import os
from pathlib import Path
from typing import List

RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "results/models",
        "results/figures",
        "tests",
        "contracts",
        "research",
        "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
