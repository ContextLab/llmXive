"""
Configuration management for the elastic anisotropy prediction pipeline.

Handles path resolution, random seed management, and API key validation.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import random
import numpy as np

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CODE_ROOT = _PROJECT_ROOT / "code"

# Default paths relative to project root
_PATHS = {
    "data_raw": _PROJECT_ROOT / "data" / "raw",
    "data_processed": _PROJECT_ROOT / "data" / "processed",
    "output": _PROJECT_ROOT / "output",
    "figures": _PROJECT_ROOT / "output" / "figures",
    "src": _CODE_ROOT / "src",
    "tests": _CODE_ROOT / "tests",
}

# Constants
DEFAULT_SEED = 42
VALIDATION_THRESHOLD = 0.1  # Variance threshold for sensitivity analysis
ANISOTROPY_LOWER_BOUND = 0.0
ANISOTROPY_UPPER_BOUND = 3.0

# Cache for configuration
_config_cache: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Load and return the main configuration dictionary.
    
    Returns:
        Dict containing paths, seeds, and constants.
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = {
            "paths": {k: str(v) for k, v in _PATHS.items()},
            "seed": DEFAULT_SEED,
            "constants": {
                "validation_threshold": VALIDATION_THRESHOLD,
                "anisotropy_lower_bound": ANISOTROPY_LOWER_BOUND,
                "anisotropy_upper_bound": ANISOTROPY_UPPER_BOUND,
            },
            "environment": {
                "mp_api_key": os.getenv("MP_API_KEY"),
                "aflow_api_key": os.getenv("AFLOW_API_KEY"),
            }
        }
    return _config_cache

def get_path(key: str) -> Path:
    """
    Retrieve a specific path by key.
    
    Args:
        key: One of 'data_raw', 'data_processed', 'output', 'figures', 'src', 'tests'.
        
    Returns:
        Path object for the requested directory.
        
    Raises:
        KeyError: If the key is not found in the configuration.
    """
    if key not in _PATHS:
        raise KeyError(f"Path key '{key}' not found in configuration. Available keys: {list(_PATHS.keys())}")
    
    path = _PATHS[key]
    # Ensure directories exist
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_api_keys() -> bool:
    """
    Check if required API keys are present in the environment.
    
    Returns:
        True if all required keys are present, False otherwise.
    """
    required_keys = ["MP_API_KEY"]
    missing = [key for key in required_keys if not os.getenv(key)]
    
    if missing:
        return False
    return True

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set the random seed for reproducibility across libraries.
    
    Args:
        seed: Integer seed value. Defaults to 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """
    Get the current default random seed.
    
    Returns:
        The default seed value (42).
    """
    return DEFAULT_SEED

def ensure_directories() -> None:
    """
    Create all required directories defined in the configuration.
    """
    for path in _PATHS.values():
        path.mkdir(parents=True, exist_ok=True)