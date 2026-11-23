"""
Seed management module for reproducibility in HEA research pipeline.

This module provides utilities to pin all random seeds for numpy, random,
and os-based randomness to ensure reproducible results across runs.
"""
import os
import random
from typing import Optional
import numpy as np
import hashlib
from datetime import datetime

# Global seed storage
_global_seed: Optional[int] = None
_seed_source: Optional[str] = None


def set_seed(seed: Optional[int] = None, seed_source: str = "default") -> int:
    """
    Set random seeds for numpy, random, and record the seed for reproducibility.
    
    Args:
        seed: The seed value. If None, generates a seed from current timestamp.
        seed_source: A descriptive string identifying the source of the seed.
        
    Returns:
        The seed value that was set.
    """
    global _global_seed, _seed_source
    
    if seed is None:
        # Generate a seed from current timestamp with microsecond precision
        # to ensure uniqueness while remaining reproducible if the timestamp is known
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        seed = int(hashlib.sha256(timestamp.encode()).hexdigest()[:8], 16)
    
    _global_seed = seed
    _seed_source = seed_source
    
    # Set numpy seed
    np.random.seed(seed)
    
    # Set random module seed
    random.seed(seed)
    
    # Log the seed setting
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Random seed set to {seed} (source: {seed_source})")
    
    return seed


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.
    
    Returns:
        The global seed value, or None if no seed has been set.
    """
    return _global_seed


def get_random_state() -> np.random.RandomState:
    """
    Get a new numpy RandomState initialized with the global seed.
    
    Returns:
        A numpy RandomState object.
    """
    if _global_seed is None:
        # If no global seed is set, generate a new one
        set_seed()
    
    return np.random.RandomState(_global_seed)


class SeedContext:
    """
    Context manager for temporary seed setting.
    
    Example:
        with SeedContext(42):
            # code that needs reproducible randomness
            pass
        # seed is restored to previous state
    """
    
    def __init__(self, seed: int):
        """
        Initialize the context manager.
        
        Args:
            seed: The seed to set within the context.
        """
        self.seed = seed
        self.previous_seed = None
        self.previous_source = None
    
    def __enter__(self):
        """Save current seed and set new one."""
        global _global_seed, _seed_source
        self.previous_seed = _global_seed
        self.previous_source = _seed_source
        set_seed(self.seed, seed_source="context_manager")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous seed."""
        global _global_seed, _seed_source
        _global_seed = self.previous_seed
        _seed_source = self.previous_source
        # Restore numpy and random states
        if self.previous_seed is not None:
            np.random.seed(self.previous_seed)
            random.seed(self.previous_seed)
        return False


def get_seed_info() -> dict:
    """
    Get information about the current seed configuration.
    
    Returns:
        A dictionary containing seed value and source.
    """
    return {
        "seed": _global_seed,
        "source": _seed_source,
        "is_set": _global_seed is not None
    }
