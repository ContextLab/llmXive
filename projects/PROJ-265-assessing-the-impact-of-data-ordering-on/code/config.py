import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    return _PROJECT_ROOT / "data"

def get_results_dir() -> Path:
    return _PROJECT_ROOT / "results"

def get_data_seed() -> int:
    return 42

def get_bootstrap_seed() -> int:
    return 42

def get_shuffle_seed() -> int:
    return 42

def ensure_directories():
    """Ensure all necessary directories exist."""
    dirs = [
        get_data_dir() / "raw",
        get_data_dir() / "processed",
        get_results_dir(),
        get_project_root() / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
