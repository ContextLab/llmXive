"""
Deterministic random seed management for reproducible experiments.

This module provides utilities to set and retrieve random seeds across
Python's random module, NumPy, and PyTorch to ensure reproducibility.
"""

import os
import random
import numpy as np
import torch
from typing import Optional

# Default seed value for reproducibility
DEFAULT_SEED = 42


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's random seeds
    torch.manual_seed(seed)
    
    # For CUDA reproducibility (if available)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    return seed


def get_seed_value() -> int:
    """
    Retrieve the current seed value from the environment or default.
    
    Returns:
        The seed value, either from the SEED environment variable
        or the DEFAULT_SEED.
    """
    env_seed = os.getenv('SEED')
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            pass
    return DEFAULT_SEED
