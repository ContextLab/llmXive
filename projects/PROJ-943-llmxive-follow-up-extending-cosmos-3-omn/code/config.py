import os
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root Configuration
# Assumes the script is run from the repository root or `code/` directory.
# We determine the base path dynamically to ensure portability.
_BASE_DIR = Path(__file__).resolve().parent.parent
if not (_BASE_DIR / "code").exists():
    # Fallback if __file__ is inside code/ directly
    _BASE_DIR = _BASE_DIR.parent

# Default configuration values
_DEFAULT_CONFIG = {
    "seed": 42,
    "device": "auto",  # "auto", "cpu", "cuda"
    "data": {
        "raw_dir": "code/data/raw",
        "processed_dir": "code/data/processed",
        "splits_dir": "code/data/splits",
        "schema_dir": "code/data/schema",
    },
    "models": {
        "output_dir": "code/models",
        "checkpoint_dir": "code/models/checkpoints",
    },
    "logs": {
        "output_dir": "code/logs",
        "memory_log": "memory_profile.log",
    },
    "training": {
        "batch_size": 32,
        "max_epochs": 10,
        "learning_rate": 1e-5,
        "max_memory_gb": 7,
    },
}

# Global config state (mutable for set_config)
_config_state: Dict[str, Any] = {}

def get_config() -> Dict[str, Any]:
    """
    Returns the current configuration dictionary.
    Loads defaults if not yet initialized.
    """
    if not _config_state:
        _config_state.update(_DEFAULT_CONFIG)
    return _config_state

def set_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Updates the global configuration with provided overrides.
    """
    if overrides:
        def _deep_update(d: Dict, u: Dict) -> Dict:
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    _deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        _deep_update(_config_state, overrides)
    return _config_state

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across libraries.
    Uses the seed from config if none provided.
    """
    cfg = get_config()
    effective_seed = seed if seed is not None else cfg.get("seed", 42)
    
    random.seed(effective_seed)
    os.environ['PYTHONHASHSEED'] = str(effective_seed)
    
    # Attempt to set seeds for numpy and torch if available
    try:
        import numpy as np
        np.random.seed(effective_seed)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(effective_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(effective_seed)
    except ImportError:
        pass

def get_path(key: str, *subpaths: str) -> Path:
    """
    Resolves a configuration path key to an absolute Path object.
    
    Args:
        key: The top-level key in config (e.g., 'data', 'models', 'logs').
        *subpaths: Additional path components to append.
    
    Returns:
        Absolute Path object.
    
    Raises:
        KeyError: If the key is not found in the configuration.
    """
    cfg = get_config()
    
    # Navigate to the specific directory path
    if key not in cfg:
        raise KeyError(f"Configuration key '{key}' not found.")
    
    base_path_str = cfg[key]
    
    # If the config value is a dict (like 'data'), look for the specific sub-key
    # or assume the key itself maps to a string if it's a direct path.
    # Based on _DEFAULT_CONFIG, 'data' is a dict, so we need the actual dir name.
    # However, the caller usually knows the specific sub-key (e.g., 'raw_dir').
    # To make this flexible, we check if the key maps to a dict.
    
    if isinstance(base_path_str, dict):
        # If the key is a dict, the caller likely passed the sub-key in *subpaths
        # or we need to handle a specific pattern.
        # Let's assume the standard usage: get_path('data', 'raw_dir')
        # But the prompt implies get_path('data') might return the base?
        # Let's implement a robust lookup:
        # If key is 'data', we expect the first subpath to be 'raw_dir', 'processed_dir', etc.
        if not subpaths:
            raise ValueError(f"Key '{key}' is a dictionary. Please specify a sub-key (e.g., 'raw_dir').")
        dir_name = subpaths[0]
        if dir_name not in base_path_str:
            raise KeyError(f"Sub-key '{dir_name}' not found in config key '{key}'.")
        path_str = base_path_str[dir_name]
        remaining = subpaths[1:]
    else:
        # Direct string path
        path_str = str(base_path_str)
        remaining = subpaths
    
    # Construct the full path relative to project root
    full_path = _BASE_DIR / path_str / Path(*remaining)
    
    return full_path

def get_device() -> str:
    """
    Determines the compute device based on configuration and hardware availability.
    
    Returns:
        "cuda" if available and configured, otherwise "cpu".
    """
    cfg = get_config()
    device_setting = cfg.get("device", "auto")
    
    if device_setting == "cpu":
        return "cpu"
    
    if device_setting == "cuda":
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            else:
                # Log warning if forced cuda but not available
                import logging
                logging.warning("CUDA requested but not available, falling back to CPU.")
                return "cpu"
        except ImportError:
            return "cpu"
    
    # Default auto behavior
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    
    return "cpu"

# Initialize config on import to ensure consistency
_config_state.update(_DEFAULT_CONFIG)
