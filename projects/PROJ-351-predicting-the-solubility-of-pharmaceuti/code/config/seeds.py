"""
Seed Management (Task T009)

Provides functions to set and retrieve random seeds for reproducibility.
"""
import os
import random
import logging
from typing import Optional
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

DEFAULT_SEED = 42
_seed = DEFAULT_SEED

def get_seed() -> int:
    """Returns the currently set seed."""
    return _seed

def set_seed(seed: int) -> None:
    """Sets the global seed and applies it to all relevant libraries."""
    global _seed
    _seed = seed
    logging.info(f"Seed set to {seed}")

def ensure_seeded(seed: Optional[int] = None) -> None:
    """
    Ensures reproducibility by setting seeds for numpy, random, and torch (if available).
    
    Args:
        seed: Optional seed value. If None, uses DEFAULT_SEED.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    set_seed(seed)
    
    # Python random
    random.seed(seed)
    
    # Numpy
    np.random.seed(seed)
    
    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    
    logging.info(f"Reproducibility seeds set to {seed} for all libraries.")
