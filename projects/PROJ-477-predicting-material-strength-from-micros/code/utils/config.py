"""
Configuration and Path Management for the Material Strength Prediction Project.
Includes seed management for reproducibility.
"""
import os
import random
from pathlib import Path
from typing import Optional

import numpy as np

# Try to import torch, but handle gracefully if not installed yet
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Cache for project root to avoid repeated filesystem checks
_PROJECT_ROOT: Optional[Path] = None


def _find_project_root() -> Path:
    """
    Finds the project root directory by looking for the 'code' and 'data' directories.
    This function is robust to the execution context (run from root, code/, or code/utils/).
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Start from the directory of this file
    current = Path(__file__).resolve()
    
    # Strategy 1: Check parents of the current file path
    # Typical path: PROJ/code/utils/config.py -> parents: code/utils, code, PROJ
    for parent in [current.parent] + list(current.parents):
        # We look for a directory that contains 'code' and 'data' as subdirectories
        # If current is PROJ/code/utils, parent is PROJ/code. 
        # We check if parent.parent has 'code' and 'data'.
        candidate = parent
        # If we are at PROJ/code, we need to go up one more level to PROJ
        if (candidate / "code").exists() and (candidate / "data").exists():
            _PROJECT_ROOT = candidate
            return candidate
        
        # Check if this candidate IS the root (contains code and data directly)
        if (candidate / "code").exists() and (candidate / "data").exists():
             _PROJECT_ROOT = candidate
             return candidate

    # Strategy 2: If we are running from a script in the root, __file__ might be relative or different.
    # Fallback: Check if 'code' and 'data' exist in current working directory
    cwd = Path.cwd()
    if (cwd / "code").exists() and (cwd / "data").exists():
        _PROJECT_ROOT = cwd
        return cwd

    # Strategy 3: Walk up from CWD if not found
    for parent in [cwd] + list(cwd.parents):
        if (parent / "code").exists() and (parent / "data").exists():
            _PROJECT_ROOT = parent
            return parent

    raise FileNotFoundError(
        "Could not determine project root. Expected 'code' and 'data' directories. "
        f"Searched: {current}, {cwd} and their parents."
    )


def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the code is run from the project root or one of its subdirectories.
    Caches the result for performance.
    """
    return _find_project_root()


def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"


def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"


def get_raw_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"


def get_results_dir() -> Path:
    """Returns the path to the results directory."""
    root = get_project_root()
    results_dir = root / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def get_code_dir() -> Path:
    """Returns the path to the code directory."""
    return get_project_root() / "code"


def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across libraries.
    
    Args:
        seed: The integer seed value to use. Defaults to 42.
    """
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's random seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # If using multi-GPU
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variable for deterministic behavior in some ops
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_seed() -> int:
    """
    Returns the default seed value used in the project.
    
    Returns:
        The default seed integer (42).
    """
    return 42