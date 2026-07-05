"""
Random seed pinning utility for reproducible experiments.

This module provides functions to set and verify random seeds across
Python's standard library, NumPy, and PyTorch to ensure deterministic
behavior during model training and evaluation.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any

import numpy as np
import torch
import torch.backends.cudnn

# Import project config to access global settings
try:
    from ..config import get_config
except (ImportError, ValueError):
    # Fallback if imported directly without package context
    def get_config():
        return {
            "random_seed": 42,
            "deterministic_mode": True
        }


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed (Optional[int]): The seed value to use. If None, uses the seed
            from the project configuration.

    Returns:
        int: The seed value that was set.

    Notes:
        - Sets seeds for python.random, numpy.random, and torch.
        - Configures PyTorch for deterministic behavior if enabled in config.
        - Sets environment variables for CuDNN determinism if applicable.
    """
    if seed is None:
        config = get_config()
        seed = config.get("random_seed", 42)

    # Ensure seed is an integer
    seed = int(seed)

    # Set Python random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch random seeds
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # For multi-GPU setups (though we are CPU-only)

    # Configure deterministic behavior
    config = get_config()
    deterministic_mode = config.get("deterministic_mode", True)

    if deterministic_mode:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ['PYTHONHASHSEED'] = str(seed)

        # Additional PyTorch settings for determinism
        if hasattr(torch, 'use_deterministic_algorithms'):
            torch.use_deterministic_algorithms(True)

    return seed


def get_seed_hash(seed: int) -> str:
    """
    Generate a hash string from a seed value for logging and experiment tracking.

    Args:
        seed (int): The seed value to hash.

    Returns:
        str: A hexadecimal hash string of the seed.
    """
    return hashlib.md5(str(seed).encode()).hexdigest()[:8]


def verify_determinism(
    func: Any,
    *args,
    seed: Optional[int] = None,
    tolerance: float = 1e-6,
    **kwargs
) -> bool:
    """
    Verify that a function produces deterministic results when seeded.

    This is a utility for testing determinism by running the function twice
    with the same seed and comparing outputs.

    Args:
        func (callable): The function to test for determinism.
        *args: Positional arguments to pass to the function.
        seed (Optional[int]): Seed to use for verification.
        tolerance (float): Tolerance for floating point comparison.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        bool: True if results are deterministic within tolerance, False otherwise.
    """
    if seed is None:
        config = get_config()
        seed = config.get("random_seed", 42)

    # Run first time
    set_seed(seed)
    result1 = func(*args, **kwargs)

    # Run second time
    set_seed(seed)
    result2 = func(*args, **kwargs)

    # Compare results
    if isinstance(result1, torch.Tensor) and isinstance(result2, torch.Tensor):
        return torch.allclose(result1, result2, atol=tolerance)
    elif isinstance(result1, np.ndarray) and isinstance(result2, np.ndarray):
        return np.allclose(result1, result2, atol=tolerance)
    else:
        # For other types, use direct comparison
        return result1 == result2


class DeterministicContext:
    """
    Context manager for temporarily setting and restoring random seeds.

    Useful for running specific operations with a different seed while
    preserving the global seed state.

    Example:
        with DeterministicContext(seed=123):
            # Code here runs with seed 123
            result = model(data)
        # Global seed state is restored here
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self._original_state = {}

    def __enter__(self):
        # Save current states
        self._original_state = {
            'random': random.getstate(),
            'numpy': np.random.get_state(),
            'torch': torch.get_rng_state()
        }

        # Set new seed if provided
        if self.seed is not None:
            set_seed(self.seed)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original states
        random.setstate(self._original_state['random'])
        np.random.set_state(self._original_state['numpy'])
        torch.set_rng_state(self._original_state['torch'])

        return False


def get_current_seeds() -> Dict[str, Any]:
    """
    Get the current state of all random number generators.

    Returns:
        Dict[str, Any]: Dictionary containing current states of random, numpy, and torch.
    """
    return {
        'python': random.getstate(),
        'numpy': np.random.get_state(),
        'torch': torch.get_rng_state().clone() if torch.cuda.is_available() else torch.get_rng_state()
    }
