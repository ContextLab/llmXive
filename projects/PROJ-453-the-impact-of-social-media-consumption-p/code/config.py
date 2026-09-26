"""
Configuration constants for the project.
"""
import os
from pathlib import Path
from typing import List, Optional

RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"

def ensure_directories() -> None:
    """
    Ensure all required project directories exist.
    """
    dirs = [
        Path(DATA_ROOT),
        Path(DATA_ROOT) / "raw",
        Path(DATA_ROOT) / "processed",
        Path(RESULTS_ROOT),
        Path(RESULTS_ROOT) / "models",
        Path(RESULTS_ROOT) / "figures",
        Path("contracts"),
        Path("tests")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
