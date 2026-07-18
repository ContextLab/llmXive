"""
Configuration management for the DomainShuttle project.

This module handles loading and validating all project settings,
including paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default Configuration
_DEFAULT_CONFIG: Dict[str, Any] = {
    "paths": {
        "project_root": str(_PROJECT_ROOT),
        "data": str(_PROJECT_ROOT / "data"),
        "raw_data": str(_PROJECT_ROOT / "data" / "raw"),
        "processed_data": str(_PROJECT_ROOT / "data" / "processed"),
        "results": str(_PROJECT_ROOT / "data" / "results"),
        "models": str(_PROJECT_ROOT / "data" / "models"),
        "logs": str(_PROJECT_ROOT / "data" / "logs"),
    },
    "seeds": {
        "global_seed": 42,
    },
    "hyperparameters": {
        "batch_size": 1,
        "learning_rate": 1e-4,
        "num_epochs": 50,
        "early_stopping_patience": 10,
    },
    "fidelity_threshold": 0.85,  # Default fallback for US3
}

# In-memory cache for the loaded config
_config_cache: Dict[str, Any] = {}

def get_config() -> Dict[str, Any]:
    """
    Retrieves the full configuration dictionary.

    Validates required keys and ensures paths exist (creating them if necessary).

    Returns:
        The validated configuration dictionary.

    Raises:
        ValueError: If 'fidelity_threshold' is missing or invalid.
    """
    if _config_cache:
        return _config_cache

    config = _DEFAULT_CONFIG.copy()

    # Validate fidelity_threshold
    if "fidelity_threshold" not in config:
        raise ValueError("Configuration error: 'fidelity_threshold' is missing.")
    
    threshold = config["fidelity_threshold"]
    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
        raise ValueError(
            f"Configuration error: 'fidelity_threshold' must be a float between 0.0 and 1.0. "
            f"Got: {threshold}"
        )

    # Ensure directories exist
    for key, path_str in config["paths"].items():
        path = Path(path_str)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

    _config_cache.update(config)
    return config
