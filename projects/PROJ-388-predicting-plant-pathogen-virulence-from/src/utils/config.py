"""
Configuration management for the Plant Pathogen Virulence Prediction Pipeline.

This module handles seed pinning for reproducibility, path management for data
and output directories, and environment variable loading.
"""

import os
import random
from pathlib import Path
from typing import Optional

# Attempt to load environment variables from a .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, ignore.
    pass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Project Root is assumed to be the directory containing 'src', 'data', etc.
# We resolve this relative to the config file location.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Seed Pinning
# Default seed if not overridden by environment variable
SEED: int = int(os.getenv("RANDOM_SEED", "42"))

# 2. Path Management
# Root directory for all data operations
DATA_ROOT: Path = _PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_ROOT / "raw"
PROCESSED_DATA_DIR: Path = DATA_ROOT / "processed"
INTERIM_DATA_DIR: Path = DATA_ROOT / "interim"

# Output directory for figures and reports
OUTPUT_ROOT: Path = _PROJECT_ROOT / "output"
FIGURES_DIR: Path = OUTPUT_ROOT / "figures"

# 3. API & Network Settings
# Timeout for network requests in seconds
API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

# Retry settings for network operations
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))

# 4. Logging
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# 5. Analysis Parameters
# Default number of permutations for FDR sensitivity check
PERMUTATIONS: int = int(os.getenv("PERMUTATIONS", "1000"))
# FDR threshold
FDR_THRESHOLD: float = float(os.getenv("FDR_THRESHOLD", "0.05"))
# Correlation threshold for visualization
CORRELATION_THRESHOLD: float = float(os.getenv("CORRELATION_THRESHOLD", "0.5"))

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).

    Args:
        seed: The integer seed value. If None, uses the global SEED constant.
    """
    if seed is None:
        seed = SEED

    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # Set deterministic behavior for CUDA if available
    try:
        import torch
        if torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

def ensure_directories() -> None:
    """
    Creates all required data and output directories if they do not exist.
    This should be called at the start of the pipeline execution.
    """
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        INTERIM_DATA_DIR,
        OUTPUT_ROOT,
        FIGURES_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_data_path(relative_path: str) -> Path:
    """
    Constructs an absolute path within the data root.

    Args:
        relative_path: Path relative to DATA_ROOT.

    Returns:
        Absolute Path object.
    """
    return DATA_ROOT / relative_path

def get_output_path(relative_path: str) -> Path:
    """
    Constructs an absolute path within the output root.

    Args:
        relative_path: Path relative to OUTPUT_ROOT.

    Returns:
        Absolute Path object.
    """
    return OUTPUT_ROOT / relative_path

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

# Ensure directories exist upon import
ensure_directories()