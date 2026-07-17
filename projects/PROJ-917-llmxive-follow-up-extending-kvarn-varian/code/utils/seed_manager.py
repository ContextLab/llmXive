"""
Random seed management for reproducibility across all modules.

This module provides a centralized way to set and retrieve random seeds
for numpy, Python's random module, and torch (if available).
"""
import random
import os
from typing import Optional
import logging

import numpy as np

# Try to import torch, but don't fail if it's not available (CPU-only environment)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

_global_seed: Optional[int] = None

def set_seed(seed: int, force: bool = False) -> None:
    """
    Set the random seed for all supported libraries to ensure reproducibility.

    Args:
        seed (int): The seed value to use.
        force (bool): If True, overwrite an existing seed. If False, raise an error
                      if a seed has already been set.
    """
    global _global_seed

    if _global_seed is not None and not force:
        if _global_seed == seed:
            logger.info(f"Seed already set to {seed}. No change needed.")
            return
        else:
            raise ValueError(
                f"Seed has already been set to {_global_seed}. "
                f"Cannot change to {seed} without force=True."
            )

    logger.info(f"Setting global seed to {seed}")
    _global_seed = seed

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set PyTorch's seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior for CUDA
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    else:
        logger.debug("PyTorch not available, skipping torch seed settings.")

def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.

    Returns:
        int or None: The global seed if set, None otherwise.
    """
    return _global_seed

def reset_seed() -> None:
    """
    Reset the global seed to None.
    """
    global _global_seed
    _global_seed = None
    logger.info("Global seed reset.")

def ensure_seed_set(seed: Optional[int] = None) -> int:
    """
    Ensure a seed is set, using the provided seed or the global seed.
    If neither is available, generate a new one.

    Args:
        seed (Optional[int]): A specific seed to use. If None, uses the global seed.

    Returns:
        int: The seed that was set.
    """
    global _global_seed

    if seed is not None:
        set_seed(seed, force=True)
        return seed

    if _global_seed is not None:
        return _global_seed

    # If no seed is set anywhere, generate a new one and set it
    new_seed = random.randint(0, 2**32 - 1)
    set_seed(new_seed, force=True)
    logger.warning(f"No seed was set. Generated and set a new random seed: {new_seed}")
    return new_seed
