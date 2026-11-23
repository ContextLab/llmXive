"""
Configuration management for paths, seeds, and constants.
"""
import os
from pathlib import Path
from typing import Final

# Random seed for reproducibility
SEED: Final[int] = 42

# Root directories
# Assumes this file is at: <project_root>/code/config.py
_CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT_DIR.parent

DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"
CODE_ROOT: Final[Path] = PROJECT_ROOT / "code"
RESULTS_ROOT: Final[Path] = DATA_ROOT / "results"
LOGS_ROOT: Final[Path] = PROJECT_ROOT / "logs"

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return PROJECT_ROOT

def ensure_directories() -> None:
    """Ensure all standard directories exist."""
    dirs = [DATA_ROOT, CODE_ROOT, RESULTS_ROOT, LOGS_ROOT, DATA_ROOT / "raw" / "stimuli", DATA_ROOT / "raw" / "responses", DATA_ROOT / "processed"]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_data_path(sub_path: str) -> Path:
    """Construct a full path relative to the data root."""
    return DATA_ROOT / sub_path
