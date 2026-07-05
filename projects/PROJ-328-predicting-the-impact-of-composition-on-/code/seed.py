"""
Seed management module for reproducible experiments.

This module provides functions to pin random seeds for numpy, python's random,
and xgboost to ensure reproducible results across runs.
"""

import random
import os

import numpy as np

# Try to import xgboost; if not available, functions will handle the absence gracefully
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for numpy, random, and xgboost to ensure reproducibility.

    Args:
        seed (int): The seed value to use. Default is 42.
    """
    # Set numpy seed
    np.random.seed(seed)

    # Set python random seed
    random.seed(seed)

    # Set xgboost seed if available
    if XGB_AVAILABLE:
        # Set environment variable for xgboost
        os.environ['XGBOOST_SEED'] = str(seed)
        # Also set the seed attribute if the module supports it
        if hasattr(xgb, 'set_config'):
            xgb.set_config(seed=seed)


def get_seed_env_vars(seed: int = 42) -> dict:
    """
    Get a dictionary of environment variables needed for reproducibility.

    Args:
        seed (int): The seed value to use. Default is 42.

    Returns:
        dict: Dictionary of environment variable names and values.
    """
    return {
        'PYTHONHASHSEED': str(seed),
        'XGBOOST_SEED': str(seed),
        'TF_DETERMINISTIC_OPS': '1',  # For TensorFlow if used later
        'CUBLAS_WORKSPACE_CONFIG': ':4096:8'  # For CUDA reproducibility if used later
    }


def apply_seed_env_vars(seed: int = 42) -> None:
    """
    Apply environment variables for reproducibility.

    Args:
        seed (int): The seed value to use. Default is 42.
    """
    env_vars = get_seed_env_vars(seed)
    for key, value in env_vars.items():
        os.environ[key] = value

# Convenience function to be called at the start of any script
def init_reproducibility(seed: int = 42) -> None:
    """
    Initialize reproducibility by setting seeds and environment variables.

    This is the recommended function to call at the beginning of any
    experiment script to ensure consistent results.

    Args:
        seed (int): The seed value to use. Default is 42.
    """
    apply_seed_env_vars(seed)
    set_seed(seed)