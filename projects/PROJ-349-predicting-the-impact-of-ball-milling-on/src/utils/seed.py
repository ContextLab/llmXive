"""
Seed management utility for reproducible experiments.

This module provides a centralized way to pin and manage all random states
across the project to ensure reproducibility.
"""
import os
import random
from typing import Optional, Dict, Any
import numpy as np

# Global seed value for the project
_PROJECT_SEED = 42
_RANDOM_STATE = np.random.RandomState(_PROJECT_SEED)


def get_seed() -> int:
    """
    Get the global project seed.
    
    Returns:
        int: The global seed value (default 42).
    """
    return _PROJECT_SEED


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the global project seed and reinitialize all random generators.
    
    Args:
        seed (int, optional): The seed value to use. If None, uses the default.
    """
    global _PROJECT_SEED, _RANDOM_STATE
    
    if seed is None:
        seed = _PROJECT_SEED
    
    _PROJECT_SEED = seed
    
    # Seed Python's random module
    random.seed(seed)
    
    # Seed NumPy's random generator
    _RANDOM_STATE = np.random.RandomState(seed)
    np.random.seed(seed)
    
    # Seed environment variable for other libraries (e.g., PyTorch, TensorFlow)
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_random_state() -> np.random.RandomState:
    """
    Get the current global NumPy random state.
    
    Returns:
        np.random.RandomState: The current random state object.
    """
    return _RANDOM_STATE


def set_random_state(state: np.random.RandomState) -> None:
    """
    Set the global NumPy random state.
    
    Args:
        state (np.random.RandomState): The random state to use.
    """
    global _RANDOM_STATE
    _RANDOM_STATE = state


def get_seed_config() -> Dict[str, Any]:
    """
    Get a configuration dictionary with all seed-related settings.
    
    Returns:
        dict: Configuration with seed values and states.
    """
    return {
        'project_seed': _PROJECT_SEED,
        'numpy_seed': _RANDOM_STATE.get_state()[1][0],  # First value of the state
        'python_seed': random.getstate()[1][0],  # First value of the state
    }


def init_seed(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize all random seeds and return the configuration.
    
    This is the main entry point for setting up reproducibility at the
    start of any experiment or script.
    
    Args:
        seed (int, optional): The seed to initialize with. Defaults to global seed.
        
    Returns:
        dict: The seed configuration after initialization.
    """
    set_seed(seed)
    return get_seed_config()