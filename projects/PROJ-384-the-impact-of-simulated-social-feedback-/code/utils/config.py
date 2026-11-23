"""
Configuration paths and constants for the project.
"""
import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
FIGURES_DIR = PROJECT_ROOT / "figures"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DIAGNOSTICS_DIR = RESULTS_DIR / "diagnostics"
SENSITIVITY_DIR = RESULTS_DIR / "sensitivity"

# Ensure directories exist
def ensure_directories():
    """Creates necessary directories if they don't exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        LOGS_DIR,
        FIGURES_DIR,
        RESULTS_DIR,
        DIAGNOSTICS_DIR,
        SENSITIVITY_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42
TORCH_SEED: Final[int] = 42

# Thresholds
VIF_LIMIT: Final[float] = 5.0
SENTIMENT_RANGE: Final[tuple] = (-1.0, 1.0)
MISSING_SENTINEL: Final[float] = -999.0