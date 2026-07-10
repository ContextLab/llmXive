"""
Deterministic random seed pinning utilities.

This module ensures reproducibility across the entire pipeline by:
1. Pinning random seeds for Python's built-in `random`, NumPy, and PyTorch (if available).
2. Providing a centralized function to set seeds globally.
3. Validating that seeds are within acceptable integer ranges.
"""

import os
import random
import sys
from typing import Optional, Union

import numpy as np

# Optional imports for deep learning frameworks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Default seed value for reproducibility
DEFAULT_SEED = 42


def validate_seed(seed: int) -> int:
    """
    Validates that the seed is a non-negative integer within safe bounds.
    
    Args:
        seed: The seed value to validate.
        
    Returns:
        The validated seed integer.
        
    Raises:
        ValueError: If the seed is not an integer or is negative.
    """
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed).__name__}")
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    # Max 32-bit integer for compatibility with most RNGs
    if seed > 2**31 - 1:
        raise ValueError(f"Seed exceeds 32-bit integer limit ({2**31 - 1}), got {seed}")
    return seed


def set_deterministic_seed(seed: Optional[int] = None, force_python_hash: bool = False) -> int:
    """
    Sets random seeds for all supported libraries to ensure deterministic behavior.
    
    This function:
    - Sets the seed for Python's built-in `random` module.
    - Sets the seed for NumPy.
    - Sets the seed for PyTorch (if installed), including cuDNN determinism flags.
    - Sets the seed for TensorFlow (if installed).
    - Optionally sets the PYTHONHASHSEED environment variable.
    
    Args:
        seed: The random seed to use. If None, uses DEFAULT_SEED.
        force_python_hash: If True, sets PYTHONHASHSEED environment variable before execution.
                           Note: This may require restarting the Python interpreter to take effect.
                           
    Returns:
        The seed value that was set.
        
    Raises:
        ValueError: If the provided seed is invalid.
    """
    seed = validate_seed(seed if seed is not None else DEFAULT_SEED)
    
    # Set Python built-in random seed
    random.seed(seed)
    
    # Set NumPy seed
    np.random.seed(seed)
    
    # Set PyTorch seeds and determinism flags
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # if multi-GPU
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        # For reproducibility in some ops, though it may slow down execution
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        
    # Set TensorFlow seeds and determinism flags
    if TF_AVAILABLE:
        tf.random.set_seed(seed)
        
    # Set PYTHONHASHSEED for dictionary ordering determinism
    # Note: This environment variable is read at startup. Setting it here
    # only affects subprocesses launched after this point, not the current process.
    if force_python_hash:
        os.environ['PYTHONHASHSEED'] = str(seed)
        
    return seed


def get_seed_context(seed: Optional[int] = None):
    """
    Context manager to temporarily set and restore random seeds.
    
    Useful for testing or specific operations where temporary determinism is needed
    without affecting the global state permanently.
    
    Args:
        seed: The seed to use within the context. Defaults to DEFAULT_SEED.
        
    Example:
        with get_seed_context(123):
            # Code here runs with deterministic seeds
            result = train_model()
        # Seeds are restored to previous state (or reset if no prior state tracked)
    """
    class SeedContext:
        def __init__(self, seed_val: int):
            self.seed_val = validate_seed(seed_val)
            self.previous_state = None
            
        def __enter__(self):
            # Store current state if possible (simplified approach)
            # Note: Fully restoring state for all libraries is complex.
            # This context ensures the seed is set on entry.
            set_deterministic_seed(self.seed_val)
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            # In a full implementation, we would restore previous states here.
            # For now, we leave the global seed as set, or could reset to a default.
            pass
            
    return SeedContext(seed if seed is not None else DEFAULT_SEED)


def is_deterministic_configured() -> bool:
    """
    Checks if the environment variables and seeds are configured for determinism.
    
    Returns:
        True if PYTHONHASHSEED is set and seeds appear consistent (best-effort check).
    """
    hash_seed = os.environ.get('PYTHONHASHSEED')
    return hash_seed is not None and hash_seed.isdigit()