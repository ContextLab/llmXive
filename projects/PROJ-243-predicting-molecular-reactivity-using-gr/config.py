"""
Configuration management for the project.
Handles random seeds, device settings, and directory paths.
"""
import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

# Default configuration
DEFAULT_CONFIG = {
    "seed": 42,
    "device": "cpu",
    "data_dir": "data",
    "code_dir": "code",
    "artifacts_dir": "artifacts",
    "tests_dir": "tests",
    "log_level": logging.INFO,
}

_config: Dict[str, Any] = {}

def get_default_config() -> Dict[str, Any]:
    """Return a copy of the default configuration."""
    return DEFAULT_CONFIG.copy()

def get_config() -> Dict[str, Any]:
    """Return the current active configuration."""
    if not _config:
        _config.update(get_default_config())
    return _config

def set_config(new_config: Dict[str, Any]) -> None:
    """Update the global configuration with new values."""
    _config.update(new_config)

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    If seed is None, uses the one from config.
    """
    config = get_config()
    if seed is None:
        seed = config.get("seed", 42)

    random.seed(seed)
    np.random.seed(seed)
    # Note: torch seed handling is done in torch-specific modules if needed

def ensure_directories() -> None:
    """
    Ensure all required directories exist based on the configuration.
    This is a helper function for setup scripts.
    """
    config = get_config()
    base_dirs = [
        config.get("data_dir"),
        config.get("code_dir"),
        config.get("artifacts_dir"),
        config.get("tests_dir"),
    ]

    # Specific subdirectories
    data_subdirs = ["raw", "processed", "assets"]
    artifacts_subdirs = ["logs", "weights", "metrics", "final_archive"]
    code_subdirs = ["data", "utils", "models"]

    for base in base_dirs:
        if base:
            os.makedirs(base, exist_ok=True)

    for subdir in data_subdirs:
        os.makedirs(os.path.join(config.get("data_dir", "data"), subdir), exist_ok=True)

    for subdir in artifacts_subdirs:
        os.makedirs(os.path.join(config.get("artifacts_dir", "artifacts"), subdir), exist_ok=True)

    for subdir in code_subdirs:
        os.makedirs(os.path.join(config.get("code_dir", "code"), subdir), exist_ok=True)