"""
Global configuration constants for the project.
"""

import os
from pathlib import Path
from typing import Final

# Project root is assumed to be the directory containing this file's parent
# Adjust if the structure is different
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
LOG_DIR: Final[Path] = PROJECT_ROOT / "data" / "logs"
MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
ERRORS_DIR: Final[Path] = PROJECT_ROOT / "errors"

# Random seed for reproducibility
RANDOM_SEED: Final[int] = 42

def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    directories = [
        DATA_DIR,
        LOG_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        ERRORS_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "curated",
        DATA_DIR / "artifacts",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
