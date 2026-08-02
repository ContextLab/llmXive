"""
Global seed management for reproducibility across all scripts.

This module provides a centralized way to set random seeds for Python's
random module, NumPy, and PyTorch to ensure reproducible results across
all scripts in the llmXive pipeline.
"""
import random
import os
from typing import Optional, List, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def set_global_seed(seed: int, deterministic: bool = True) -> None:
    """
    Set seeds for all random number generators to ensure reproducibility.
    
    This function configures:
    - Python's built-in random module
    - NumPy's random number generator
    - PyTorch's CPU and GPU random states (if available)
    - Environment variables for deterministic behavior
    
    Args:
        seed (int): The random seed to use. Must be a non-negative integer.
        deterministic (bool): If True, enforce deterministic behavior in PyTorch.
            This may impact performance but ensures reproducible results.
            
    Raises:
        ValueError: If seed is negative or not an integer.
        RuntimeError: If deterministic mode is requested but not supported.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy seed
    if HAS_NUMPY:
        np.random.seed(seed)
    
    # Set PyTorch seeds
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            
            if deterministic:
                # Deterministic behavior settings
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                # Set workspace configuration for cuBLAS
                os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    
    # Set environment variable for Python hashing
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Log the seed setting for debugging purposes
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Global seed set to {seed}")
    logger.info(f"NumPy available: {HAS_NUMPY}")
    logger.info(f"PyTorch available: {HAS_TORCH}")
    if HAS_TORCH and torch.cuda.is_available():
        logger.info(f"PyTorch using CUDA: {torch.cuda.get_device_name(0)}")


def get_seed() -> Optional[int]:
    """
    Retrieve the current seed from the environment variable.
    
    Returns:
        Optional[int]: The seed value if set in environment, None otherwise.
    """
    seed_str = os.environ.get('PYTHONHASHSEED')
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            return None
    return None


def reset_seed() -> None:
    """
    Reset all random seeds to a default state (None).
    
    This clears the PYTHONHASHSEED environment variable and does not
    explicitly reset random number generators, as they cannot be reset
    to a "None" state.
    """
    if 'PYTHONHASHSEED' in os.environ:
        del os.environ['PYTHONHASHSEED']
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Global seed cleared")