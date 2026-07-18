"""
Configuration management for the Elastic Anisotropy prediction pipeline.

Handles paths, random seeds, constants, and API key validation.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import random
import numpy as np

# Project root is assumed to be the directory containing 'code'
# If running as a module, we resolve relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Default random seed as per specification
DEFAULT_SEED = 42

# Constants
# Physical bounds for Anisotropy A1 (Zener anisotropy ratio for cubic crystals)
# Theoretical range is often cited as 0 < A1 < 3 for stability in this context,
# though strictly A1 > 0 for stability. We use the task-specified range.
ANISOTROPY_LOWER_BOUND = 0.0
ANISOTROPY_UPPER_BOUND = 3.0

# Path configuration
_PATHS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "output": "output",
    "figures": "output/figures",
    "models": "output/models",
    "specs": "specs",
}

def _get_project_root() -> Path:
    """Returns the project root path."""
    return _PROJECT_ROOT

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary containing all configuration settings.
    
    Returns:
        dict: Configuration dictionary with paths, seed, and constants.
    """
    root = _get_project_root()
    return {
        "root": root,
        "seed": get_seed(),
        "paths": {
            key: root / path for key, path in _PATHS.items()
        },
        "constants": {
            "anisotropy_lower_bound": ANISOTROPY_LOWER_BOUND,
            "anisotropy_upper_bound": ANISOTROPY_UPPER_BOUND,
        }
    }

def get_path(key: str, relative: Optional[Path] = None) -> Path:
    """
    Returns the absolute path for a given configuration key.
    
    Args:
        key: The key from the _PATHS dictionary (e.g., 'data_raw').
        relative: Optional relative sub-path to append.
        
    Returns:
        pathlib.Path: The absolute path.
        
    Raises:
        KeyError: If the key is not found in configuration.
    """
    root = _get_project_root()
    if key not in _PATHS:
        raise KeyError(f"Path key '{key}' not found in configuration. Available keys: {list(_PATHS.keys())}")
    
    base_path = root / _PATHS[key]
    if relative:
        return base_path / relative
    return base_path

def ensure_directories() -> None:
    """
    Creates all necessary directories defined in the configuration.
    """
    root = _get_project_root()
    for path_key, rel_path in _PATHS.items():
        dir_path = root / rel_path
        dir_path.mkdir(parents=True, exist_ok=True)

def validate_api_keys() -> None:
    """
    Validates the presence of required API keys in environment variables.
    
    Raises:
        ValueError: If a required API key is missing.
    """
    required_keys = ["MP_API_KEY"]
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    
    if missing_keys:
        raise ValueError(
            f"Missing required API keys: {', '.join(missing_keys)}. "
            "Please set them in your environment or .env file."
        )

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across random, numpy, and torch (if available).
    
    Args:
        seed: The seed value. Defaults to DEFAULT_SEED if None.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch is not required, so ignore if missing

def get_seed() -> int:
    """
    Returns the current default random seed.
    
    Returns:
        int: The seed value.
    """
    return DEFAULT_SEED

def get_constants() -> Dict[str, float]:
    """
    Returns the physical constants configuration.
    
    Returns:
        dict: Dictionary of physical constants.
    """
    return {
        "anisotropy_lower_bound": ANISOTROPY_LOWER_BOUND,
        "anisotropy_upper_bound": ANISOTROPY_UPPER_BOUND,
    }
