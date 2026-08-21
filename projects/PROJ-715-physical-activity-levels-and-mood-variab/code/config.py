"""
Configuration module for the Physical Activity and Mood Variability project.

Defines paths, random seeds, constants, and OSF dataset DOI.
"""
import os
import random
import logging
from pathlib import Path
from typing import Union, List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-715-physical-activity-levels-and-mood-variab"

# Random seed for reproducibility
RANDOM_SEED = 42

# Constants for preprocessing and analysis
MISSINGNESS_THRESHOLD = 0.2  # Threshold for missing data handling
BOOTSTRAP_ITERATIONS = 1000  # Number of bootstrap iterations for sensitivity analysis

# OSF DOI for the StudentLife dataset
OSF_DOI = "10.17605/OSF.IO/XXXXX"  # Replace with actual DOI when available
OSF_DOWNLOAD_URL = f"https://osf.io/download/{OSF_DOI}"

# Initialize logger
def init_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Initialize a logger with the specified name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Set random seed for reproducibility
def set_random_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seed for numpy, random, and tensorflow (if available)."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass

# Flexible path resolution
def get_path(*args) -> str:
    """
    Resolve file paths relative to the project root.

    Accepts multiple calling patterns:
      - get_path('data/processed', 'file.csv') -> PROJECT_ROOT/data/processed/file.csv
      - get_path('data', 'processed', 'file.csv') -> PROJECT_ROOT/data/processed/file.csv
      - get_path('data/processed/file.csv') -> PROJECT_ROOT/data/processed/file.csv

    Args:
        *args: Path components as strings.

    Returns:
        str: Absolute path to the file/directory.
    """
    # If a single argument is provided and contains separators, treat as a single path
    if len(args) == 1 and '/' in args[0]:
        path_str = args[0]
    else:
        # Join multiple arguments with '/'
        path_str = os.path.join(*args)

    # Resolve relative to project root
    return str(PROJECT_ROOT / path_str)

# Ensure directories exist
def ensure_dirs(*paths: str) -> None:
    """
    Ensure that the specified directories exist, creating them if necessary.

    Args:
        *paths: Directory paths relative to the project root.
    """
    for path in paths:
        dir_path = Path(get_path(path))
        dir_path.mkdir(parents=True, exist_ok=True)
