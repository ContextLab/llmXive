"""
Configuration management module.
Handles random seeds, hyperparameters, and path configurations.
"""
import os
import random
import numpy as np
from typing import Dict, Any, Optional
import json

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "random_seed": 42,
    "data_paths": {
        "raw": "data/raw",
        "processed": "data/processed",
        "results": "results"
    },
    "model_params": {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    }
}

def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieves a configuration value by key.
    Supports dot notation for nested keys (e.g., 'model_params.n_estimators').
    """
    keys = key.split('.')
    value = DEFAULT_CONFIG
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def save_config(filepath: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Saves the current configuration to a JSON file.
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=4)