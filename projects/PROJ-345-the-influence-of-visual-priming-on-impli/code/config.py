"""
Configuration module for the Visual Priming project.

Defines base paths for data directories, state management, and
ensures reproducibility by pinning random seeds across libraries.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# Project Root (assumed to be the directory containing 'code' and 'data')
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Base Directory Paths
_PATHS: Dict[str, Path] = {
    "raw": _PROJECT_ROOT / "data" / "raw",
    "processed": _PROJECT_ROOT / "data" / "processed",
    "primes": _PROJECT_ROOT / "data" / "primes",
    "targets": _PROJECT_ROOT / "data" / "targets",
    "state": _PROJECT_ROOT / "state" / "projects" / "PROJ-345",
}

# Default Random Seed for Reproducibility
_RANDOM_SEED: int = 42

def ensure_directories() -> None:
    """
    Creates all base data and state directories if they do not exist.
    
    This function is idempotent and safe to call multiple times.
    """
    for path in _PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_path(key: str) -> Path:
    """
    Retrieves the Path object for a given directory key.
    
    Args:
        key: The directory identifier (e.g., 'raw', 'processed', 'primes').
            
    Returns:
        The absolute Path object.
        
    Raises:
        KeyError: If the key is not recognized.
    """
    if key not in _PATHS:
        raise KeyError(f"Unknown path key: {key}. Available keys: {list(_PATHS.keys())}")
    return _PATHS[key]

def get_all_base_paths() -> Dict[str, Path]:
    """
    Returns a copy of all configured base paths.
    
    Returns:
        Dictionary mapping directory keys to Path objects.
    """
    return _PATHS.copy()

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across Python, NumPy, and random modules.
    
    Args:
        seed: The integer seed to use. If None, uses the default _RANDOM_SEED.
    """
    if seed is None:
        seed = _RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Log the seed setting for audit purposes (using standard print or logging if configured)
    # We avoid importing logging here to prevent circular dependencies during early init
    # unless explicitly needed.
    
def get_seed() -> int:
    """
    Returns the currently configured random seed.
    
    Returns:
        The integer seed value.
    """
    return _RANDOM_SEED