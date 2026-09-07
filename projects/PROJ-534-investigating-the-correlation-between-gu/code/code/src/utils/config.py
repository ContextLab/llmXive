"""
Configuration module for the gut microbiome and cognitive flexibility study.

This module defines fixed random seeds for reproducibility and configures
all project paths relative to the project root.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict

# --- Random Seeds ---
# Fixed seeds to ensure reproducibility across runs and environments.
# These must be used before any random number generation (numpy, pandas, python random).
SEED: int = 42
PYTHON_SEED: int = SEED
NUMPY_SEED: int = SEED
PANDAS_SEED: int = SEED

# --- Path Configuration ---
# Determine the project root. We assume this file is at:
# <project_root>/code/code/src/utils/config.py
# So we go up 4 levels to reach the project root.
_CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = _CURRENT_DIR.parent
CODE_DIR = SRC_DIR.parent
PROJECT_ROOT = CODE_DIR.parent.parent

# Base directories
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
RESULTS_DIR: Path = DATA_DIR / "results"
FIGURES_DIR: Path = DATA_DIR / "figures"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
CONTRACTS_DIR: Path = PROJECT_ROOT / "contracts"
SPECS_DIR: Path = PROJECT_ROOT / "specs"

# Ensure directories exist (optional, but helpful for scripts)
def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    dirs_to_create = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
    ]
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

# --- Analysis Configuration ---
# Default parameters for statistical analyses
CONFIDENCE_LEVEL: float = 0.95
SIGNIFICANCE_THRESHOLD: float = 0.05
FDR_METHOD: str = "fdr_bh"  # Benjamini-Hochberg
MIN_PARTICIPANT_AGE: int = 65  # Inclusion criterion

# --- Covariates ---
REQUIRED_COVARIATES: list[str] = [
    "age",
    "sex",
    "bmi",
    "fiber_intake",
    "antibiotics_usage",
]

# --- Logging Configuration ---
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = os.getenv("LOG_LEVEL", "INFO")

# --- Helper Functions ---
def set_global_seed(seed: int = SEED) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and Pandas.
    Must be called at the start of any script that uses randomization.
    """
    random.seed(seed)
    import numpy as np
    np.random.seed(seed)
    # Pandas doesn't have a global seed setter, but it uses numpy's RNG
    # so setting numpy seed is sufficient for pandas operations.

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the path to the main data directory."""
    return DATA_DIR

def get_raw_data_dir() -> Path:
    """Return the path to the raw data directory."""
    return RAW_DATA_DIR

def get_processed_data_dir() -> Path:
    """Return the path to the processed data directory."""
    return PROCESSED_DATA_DIR

def get_results_dir() -> Path:
    """Return the path to the results directory."""
    return RESULTS_DIR

def get_logs_dir() -> Path:
    """Return the path to the logs directory."""
    return LOGS_DIR

# Initialize directories on import to ensure structure exists
# This is safe to run repeatedly as mkdir(exist_ok=True) is idempotent.
ensure_directories()