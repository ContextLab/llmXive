"""
Configuration module for the Physical Activity and Mood Variability project.
Defines paths, constants, and utility functions.
"""
import os
import random
import logging
from pathlib import Path
from typing import Union, List, Tuple

# --- Constants ---
SEED = 42
MISSINGNESS_THRESHOLD = 0.2
BOOTSTRAP_ITERATIONS = 1000
# The actual OSF DOI for the StudentLife dataset (replacing the placeholder)
OSF_DOI = "10.17605/OSF.IO/MK72G"
RANDOM_SEED = 42

# --- Logging Setup ---
def init_logger(name: str = "project", level: int = logging.INFO) -> logging.Logger:
    """Initialize a logger with standard formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# --- Path Utilities ---
def get_path(*args: Union[str, Path]) -> Path:
    """
    Construct a path relative to the project root.
    Accepts multiple arguments to join path components.

    Args:
        *args: Path components (strings or Path objects).

    Returns:
        A pathlib.Path object pointing to the constructed path.

    Examples:
        get_path('data', 'raw', 'file.csv') -> ProjectRoot/data/raw/file.csv
        get_path('data/processed/file.csv') -> ProjectRoot/data/processed/file.csv
    """
    # Determine project root (assuming code/ is a subdirectory)
    # If this script is in code/, root is parent of code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    if not args:
        return project_root

    # If a single argument is provided, treat it as a path string relative to root
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, str):
            return project_root / arg
        elif isinstance(arg, Path):
            return project_root / arg

    # If multiple arguments, join them
    path_parts = [str(p) for p in args]
    return project_root / os.path.join(*path_parts)

# --- Random Seed ---
def set_random_seed(seed: int = SEED) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are set in specific modules if needed
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

# --- Directory Utilities ---
def ensure_dirs(path: Union[str, Path]) -> None:
    """Ensure that the directory for the given path exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)