"""
Configuration and reproducibility setup.
"""
import os
import random
import numpy as np
from typing import Dict, Any

# Global configuration state
_config = {
    "seed": 42,
    "cpu_only": True,
    "planck_map_id": "COM_CMB_IQU-IntensIQU-2048_R2.00.fits",
    "bicep_url": "https://api.bicepkeck.org/v1/spectra",
    "n_live_points": 50,
    "max_iterations": 10000
}

def init_reproducibility(seed: int = 42):
    """
    Initialize random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    _config["seed"] = seed
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_config() -> Dict[str, Any]:
    """
    Return the current configuration dictionary.
    """
    return _config.copy()

def update_config(key: str, value: Any):
    """
    Update a configuration value.
    """
    _config[key] = value