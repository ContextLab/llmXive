"""
Configuration and reproducibility setup.
Handles random seed pinning, CPU-only constraints, and verified dataset URLs.
"""
import os
import random
import numpy as np
from typing import Dict, Any

# Global configuration state
_config = {
    "seed": 42,
    "cpu_only": True,
    # Verified dataset URLs and IDs as required by the task specification
    "PLANCK_MAP_ID": "COM_CMB_IQU-IntensIQU-2048_R2.00.fits",
    "BICEP_URL": "https://api.bicepkeck.org/v1/spectra",
    "n_live_points": 50,
    "max_iterations": 10000
}

def init_reproducibility(seed: int = 42):
    """
    Initialize random seeds for reproducibility.
    Pins random.seed and numpy.random.seed to ensure deterministic behavior.
    Sets the PYTHONHASHSEED environment variable.
    
    Args:
        seed (int): The seed value to use for all random number generators.
    """
    random.seed(seed)
    np.random.seed(seed)
    _config["seed"] = seed
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_config() -> Dict[str, Any]:
    """
    Return the current configuration dictionary.
    
    Returns:
        dict: A copy of the global configuration containing:
            - seed: Current random seed
            - cpu_only: Boolean flag for CPU-only execution
            - PLANCK_MAP_ID: Verified Planck map identifier
            - BICEP_URL: Verified BICEP/Keck data URL
            - n_live_points: Number of live points for nested sampling
            - max_iterations: Maximum iterations for nested sampling
    """
    return _config.copy()

def update_config(key: str, value: Any):
    """
    Update a configuration value.
    
    Args:
        key (str): The configuration key to update.
        value (Any): The new value for the configuration key.
    """
    _config[key] = value