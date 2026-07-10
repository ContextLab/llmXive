"""
Seed management module for reproducible experiments.
Pins all random seeds for numpy, python random, and torch (if available).
"""
import os
import random
from typing import Optional

import numpy as np

# Optional imports for deep learning frameworks (not used in this CPU-only project,
# but included for completeness if dependencies are added later)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    tf = None

# Default seed value used across the project
DEFAULT_SEED = 42

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Python's built-in random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch (if available)
    if TORCH_AVAILABLE and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # TensorFlow (if available)
    if TF_AVAILABLE and tf is not None:
        tf.random.set_seed(seed)

    # Set environment variable for some libraries that read it
    os.environ['PYTHONHASHSEED'] = str(seed)

    return seed

def get_seed() -> int:
    """
    Get the currently configured seed.
    Note: This returns the last set seed or DEFAULT_SEED. It does not
    introspect the current state of random number generators.
    """
    # Try to read from environment variable first if set
    env_seed = os.environ.get('PYTHONHASHSEED')
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            pass
    return DEFAULT_SEED

class SeedContext:
    """
    Context manager to temporarily set a seed and restore it afterwards.
    """
    def __init__(self, seed: Optional[int] = None):
        self.target_seed = seed if seed is not None else DEFAULT_SEED
        self.original_seed = None

    def __enter__(self):
        # Store current seed state (simplified: just store the last used seed)
        self.original_seed = get_seed()
        set_seed(self.target_seed)
        return self.target_seed

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original seed
        set_seed(self.original_seed)
        return False