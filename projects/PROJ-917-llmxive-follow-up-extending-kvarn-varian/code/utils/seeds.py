"""
Global random seed management for reproducible experiments.

This module provides functions to set and manage random seeds across
numpy, torch, and the standard random module to ensure deterministic
behavior in simulations and data generation.
"""

import random
import os
from typing import Optional, Dict, Any

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Global seed state
_global_seed: Optional[int] = None
_is_seed_set: bool = False


def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for all relevant libraries.

    This function ensures reproducibility by setting seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (if available)
    - Environment variables for CUDA determinism

    Args:
        seed: The integer seed value to use.
    """
    global _global_seed, _is_seed_set

    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)}")

    _global_seed = seed
    _is_seed_set = True

    # Set Python random seed
    random.seed(seed)

    # Set NumPy seed
    np.random.seed(seed)

    # Set PyTorch seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        # For CUDA operations
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior
            os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
            os.environ['PYTHONHASHSEED'] = str(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.

    Returns:
        The global seed value if set, None otherwise.
    """
    return _global_seed


def ensure_seed_set(default_seed: int = 42) -> int:
    """
    Ensure a seed is set, using a default if none exists.

    Args:
        default_seed: The seed to use if no global seed is set.

    Returns:
        The seed value that is currently active.
    """
    if not _is_seed_set:
        set_global_seed(default_seed)
    return _global_seed  # type: ignore


def reset_seed() -> None:
    """Reset the global seed state."""
    global _global_seed, _is_seed_set
    _global_seed = None
    _is_seed_set = False


def get_seed_context(seed: int):
    """
    Context manager for temporary seed setting.

    Args:
        seed: The seed to use within the context.

    Returns:
        A context manager that sets and restores the seed.
    """
    class SeedContext:
        def __init__(self, temp_seed: int):
            self.temp_seed = temp_seed
            self.original_seed = _global_seed
            self.was_set = _is_seed_set

        def __enter__(self):
            set_global_seed(self.temp_seed)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            global _global_seed, _is_seed_set
            _global_seed = self.original_seed
            _is_seed_set = self.was_set
            return False

    return SeedContext(seed)


def get_seed_info() -> Dict[str, Any]:
    """
    Get information about the current seed state.

    Returns:
        A dictionary containing seed information.
    """
    return {
        "seed": _global_seed,
        "is_set": _is_seed_set,
        "torch_available": TORCH_AVAILABLE
    }
