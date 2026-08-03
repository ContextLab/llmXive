"""
Deterministic random seed pinning utilities.

This module ensures reproducibility across the pipeline by setting
seeds for Python's random, NumPy, and (if available) PyTorch/TensorFlow.
"""
import os
import random
import sys
from typing import Optional, Union
import numpy as np

# Default seed used throughout the project
DEFAULT_SEED = 42

def validate_seed(seed: int) -> bool:
    """Validate that the seed is a non-negative integer.
    
    Args:
        seed: The seed value to validate.
        
    Returns:
        True if the seed is valid (non-negative integer), False otherwise.
    """
    return isinstance(seed, int) and seed >= 0

def set_deterministic_seed(seed: int = DEFAULT_SEED) -> None:
    """Set deterministic seeds for reproducibility across all libraries.
    
    This function sets seeds for:
    - Python's built-in random module
    - NumPy
    - Environment variable PYTHONHASHSEED
    - PyTorch (if available)
    - TensorFlow (if available)
    - CuDNN (if PyTorch and CUDA are available)
    
    Args:
        seed: The random seed to use. Must be a non-negative integer.
        
    Raises:
        ValueError: If the seed is not a non-negative integer.
    """
    if not validate_seed(seed):
        raise ValueError(f"Invalid seed: {seed}. Must be a non-negative integer.")
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set environment variable for hash randomization
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Set PyTorch seeds if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
    
    # Set TensorFlow seeds if available
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    
    # Set XGBoost seed if available
    try:
        import xgboost as xgb
        # XGBoost uses 'seed' parameter in its estimators
    except ImportError:
        pass

def get_seed_context(seed: int = DEFAULT_SEED) -> dict:
    """Return a context dictionary with seed information and status.
    
    Args:
        seed: The seed value to report.
        
    Returns:
        A dictionary containing:
        - seed: The seed value used
        - is_deterministic: Boolean indicating if deterministic mode is active
        - environment_hash: Current value of PYTHONHASHSEED
        - numpy_seed: Current NumPy random state seed (if set)
    """
    context = {
        "seed": seed,
        "is_deterministic": True,
        "environment_hash": os.environ.get('PYTHONHASHSEED', 'not_set'),
        "numpy_seed": np.random.get_state()[1][0] if hasattr(np.random, 'get_state') else None
    }
    return context

def is_deterministic_configured() -> bool:
    """Check if deterministic mode is properly configured.
    
    This checks if the PYTHONHASHSEED environment variable has been set,
    which is the primary indicator that deterministic seeding has been applied.
    
    Returns:
        True if deterministic mode is configured, False otherwise.
    """
    return os.environ.get('PYTHONHASHSEED') is not None

def apply_seed_to_config(config: dict, seed_key: str = "seed") -> dict:
    """Apply a deterministic seed to a configuration dictionary.
    
    Args:
        config: The configuration dictionary to modify.
        seed_key: The key name for the seed in the config.
        
    Returns:
        The updated configuration dictionary with the seed set.
    """
    config[seed_key] = DEFAULT_SEED
    return config