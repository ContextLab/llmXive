"""
Configuration management for the elastic anisotropy pipeline.

Manages paths, random seeds, and constants.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import random
import numpy as np

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default configuration
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "output": "output",
        "figures": "output/figures"
    },
    "seeds": {
        "random": 42,
        "numpy": 42
    },
    "constants": {
        "atomic_masses": {},  # Will be populated if needed
        "element_properties": {}
    }
}

_config: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get the configuration dictionary.
    
    Returns:
        Configuration dictionary with paths, seeds, and constants.
    """
    global _config
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
        _config["paths"] = {k: str(PROJECT_ROOT / v) for k, v in _config["paths"].items()}
    return _config

def get_path(section: str, key: Optional[str] = None) -> Path:
    """
    Get a path from the configuration.
    
    Args:
        section: Configuration section (e.g., 'paths').
        key: Specific key within the section (optional).
        
    Returns:
        Path object for the requested configuration value.
        
    Raises:
        KeyError: If the section or key is not found.
    """
    config = get_config()
    if section not in config:
        raise KeyError(f"Configuration section '{section}' not found")
    
    if key is None:
        return Path(config[section])
    
    if key not in config[section]:
        raise KeyError(f"Configuration key '{key}' not found in section '{section}'")
    
    return Path(config[section][key])

def ensure_directories(paths: list) -> None:
    """
    Ensure that the given directories exist, creating them if necessary.
    
    Args:
        paths: List of path strings or Path objects.
    """
    for p in paths:
        path = Path(p) if isinstance(p, str) else p
        path.mkdir(parents=True, exist_ok=True)

def validate_api_keys() -> bool:
    """
    Validate that required API keys are set in the environment.
    
    Returns:
        True if all required keys are present, False otherwise.
    """
    required_keys = ["MP_API_KEY"]
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    
    if missing_keys:
        return False
    return True

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value. If None, uses the configured seed.
    """
    if seed is None:
        seed = get_seed()
    
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> int:
    """
    Get the configured random seed.
    
    Returns:
        Random seed value.
    """
    config = get_config()
    return config["seeds"]["random"]

def get_constants() -> Dict[str, Any]:
    """
    Get the constants dictionary.
    
    Returns:
        Constants dictionary.
    """
    config = get_config()
    return config["constants"]
