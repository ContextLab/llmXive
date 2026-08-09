"""
Configuration management for the statistical robustness project.
Handles random seed management, global constants, and path resolution.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional

# Global project root
_PROJECT_ROOT: Optional[Path] = None
_SEED: int = 42

# Global constants based on specification
ALPHA_LEVEL: float = 0.05
MIN_SERIES_LENGTH: int = 25
STATIONARITY_THRESHOLD: float = 0.05
HURST_TARGET_TOLERANCE: float = 0.05
MEAN_TARGET_TOLERANCE: float = 0.01
MAX_DIFFERENCING_ITERATIONS: int = 5
VARIANCE_INFLATION_THRESHOLD: float = 10.0

# Data directories relative to project root
DATA_DIRS: Dict[str, str] = {
    "raw": "data/raw",
    "processed": "data/processed",
    "results": "data/results",
    "null_distributions_real": "data/processed/null_distributions/real",
    "null_distributions_synthetic": "data/processed/null_distributions/synthetic",
}

# Analysis constants
SYNTHETIC_H_VALUES: list = [0.5, 0.7, 0.8, 0.9]
SYNTHETIC_LENGTHS: list = [100, 500, 1000, 5000, 10000]
MONTE_CARLO_TRIALS_DEFAULT: int = 1000

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root.
    If not set, infers it from the current working directory.
    """
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Assume standard project structure: code/ is at root or src/ is at root
        # Based on tasks.md, root contains code/, data/, tests/, specs/
        # We infer root as the parent of 'code' or current dir if 'code' doesn't exist
        current = Path.cwd()
        if (current / "code").exists():
            _PROJECT_ROOT = current
        elif (current / "src").exists() and (current / "data").exists():
            # If we are inside code/src, go up twice
            _PROJECT_ROOT = current.parent.parent
        else:
            _PROJECT_ROOT = current
    return _PROJECT_ROOT

def set_project_root(path: Path) -> None:
    """
    Explicitly set the project root directory.
    """
    global _PROJECT_ROOT
    _PROJECT_ROOT = Path(path).resolve()

def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path against the project root.
    """
    root = get_project_root()
    return root / relative_path

def ensure_dirs() -> None:
    """
    Creates all required directories defined in DATA_DIRS.
    """
    root = get_project_root()
    for dir_name, rel_path in DATA_DIRS.items():
        dir_path = root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across numpy, python random, and torch (if available).
    Updates the global _SEED constant.
    """
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """
    Returns the currently set random seed.
    """
    return _SEED

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary of all global configuration constants.
    """
    return {
        "project_root": str(get_project_root()),
        "seed": _SEED,
        "alpha_level": ALPHA_LEVEL,
        "min_series_length": MIN_SERIES_LENGTH,
        "stationarity_threshold": STATIONARITY_THRESHOLD,
        "hurst_target_tolerance": HURST_TARGET_TOLERANCE,
        "mean_target_tolerance": MEAN_TARGET_TOLERANCE,
        "max_differencing_iterations": MAX_DIFFERENCING_ITERATIONS,
        "variance_inflation_threshold": VARIANCE_INFLATION_THRESHOLD,
        "synthetic_h_values": SYNTHETIC_H_VALUES,
        "synthetic_lengths": SYNTHETIC_LENGTHS,
        "monte_carlo_trials_default": MONTE_CARLO_TRIALS_DEFAULT,
        "data_dirs": DATA_DIRS,
    }