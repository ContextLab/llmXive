"""
Configuration management for the Epigenetic Drift project.

Handles path management, random seeds, and environment variable loading.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# --- Project Root & Path Constants ---
# Determine project root based on the standard directory structure expected by tasks.md
# Assuming this file is at code/config.py, root is two levels up
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_DIR = _PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = _PROJECT_ROOT / "output"
OUTPUT_FIGURES_DIR = OUTPUT_DIR / "figures"
LOGS_DIR = _PROJECT_ROOT / "logs"
SPECS_DIR = _PROJECT_ROOT / "specs"

# Output File Paths (referenced in tasks.md)
DISCOVERY_RESULTS_PATH = OUTPUT_DIR / "discovery_results.json"
DISCOVERY_STATUS_PATH = OUTPUT_DIR / "discovery_status.json"
VARIANCE_MATRIX_PATH = DATA_PROCESSED_DIR / "variance_matrix.csv"
CORRELATION_RESULTS_PATH = OUTPUT_DIR / "correlation_results.json"
TIMESCALE_ALIGNMENT_PATH = OUTPUT_DIR / "timescale_alignment.json"
FINAL_REPORT_PATH = OUTPUT_DIR / "final_report.json"
VERIFIED_DATASETS_PATH = DATA_DIR / "verified_datasets.yaml"

# --- Random Seeds ---
# Centralized seed management for reproducibility
DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Attempt to set torch seed if available, ignore if not (CPU-only constraint)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not installed, which is acceptable per CPU-only constraints

# --- Environment Variables ---
def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Safely retrieves an environment variable.
    
    Args:
        key: The environment variable name.
        default: Default value if the key is not found.
        
    Returns:
        The environment variable value or the default.
    """
    return os.getenv(key, default)

def get_env_int(key: str, default: int = 0) -> int:
    """Retrieves an environment variable as an integer."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Retrieves an environment variable as a float."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default

# --- Runtime Configuration ---
# These can be overridden by environment variables for CI/CD or specific runs

# Maximum runtime in seconds (6 hours as per task T019 constraints)
MAX_RUNTIME_SECONDS = get_env_int("MAX_RUNTIME_SECONDS", 6 * 60 * 60)

# Memory limit in GB (2GB as per constraints)
MEMORY_LIMIT_GB = get_env_float("MEMORY_LIMIT_GB", 2.0)

# GEO/ENCODE API timeout in seconds
API_TIMEOUT = get_env_int("API_TIMEOUT", 30)

# Random seed for the current run
RUN_SEED = get_env_int("RUN_SEED", DEFAULT_SEED)

# --- Initialization ---
def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    This should be called at the start of the pipeline or setup.
    """
    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_DIR,
        OUTPUT_FIGURES_DIR,
        LOGS_DIR,
        SPECS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize seed immediately upon import if RUN_SEED is set, 
# or defer to explicit set_seed() call. 
# For safety in library usage, we do not auto-seed here unless explicitly requested via env.
if get_env("AUTO_SEED", "false").lower() == "true":
    set_seed(RUN_SEED)