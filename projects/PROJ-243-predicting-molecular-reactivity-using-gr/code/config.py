import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

# Default configuration
DEFAULT_CONFIG = {
    "base_dir": os.getcwd(),
    "random_seed": 42,
    "device": "cpu",
    "log_level": "INFO",
    "data_dir": "data",
    "code_dir": "code",
    "artifacts_dir": "artifacts",
    "tests_dir": "tests",
}

_config: Dict[str, Any] = {}

def get_default_config() -> Dict[str, Any]:
    """Return a copy of the default configuration."""
    return DEFAULT_CONFIG.copy()

def get_config() -> Dict[str, Any]:
    """Return the current configuration, merging defaults with any overrides."""
    if not _config:
        _config.update(DEFAULT_CONFIG)
    return _config

def set_config(new_config: Dict[str, Any]) -> None:
    """Update the current configuration with new values."""
    global _config
    if not _config:
        _config.update(DEFAULT_CONFIG)
    _config.update(new_config)

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_config().get("random_seed", 42)
    
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch seed setting would go here if torch is imported and available
    # try:
    #     import torch
    #     torch.manual_seed(seed)
    #     if torch.cuda.is_available():
    #         torch.cuda.manual_seed_all(seed)
    # except ImportError:
    #     pass

def ensure_directories(dirs: list) -> None:
    """
    Ensure that a list of directory paths exist relative to the base_dir.
    Creates them if they don't exist.
    """
    base_dir = get_config().get("base_dir", os.getcwd())
    for d in dirs:
        full_path = os.path.join(base_dir, d)
        os.makedirs(full_path, exist_ok=True)
        # logging.info(f"Ensured directory: {full_path}")

# Initialize config on import to ensure defaults are available
_config = DEFAULT_CONFIG.copy()