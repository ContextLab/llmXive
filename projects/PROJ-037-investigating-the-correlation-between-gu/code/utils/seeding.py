"""
Random seed management for reproducibility.
"""
import random
import os
from typing import Optional

import numpy as np

class SeedManager:
    """
    Manages random seeds for numpy, python random, and os environment.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._set_seeds()

    def _set_seeds(self) -> None:
        """Set seeds for all random number generators."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        os.environ["PYTHONHASHSEED"] = str(self.seed)

    def set_seed(self, seed: int) -> None:
        """Update the seed and re-apply to all generators."""
        self.seed = seed
        self._set_seeds()

_global_seed_manager: Optional[SeedManager] = None

def set_seed(seed: int = 42) -> SeedManager:
    """
    Initialize or update the global seed manager.

    Args:
        seed: The random seed to use.

    Returns:
        The SeedManager instance.
    """
    global _global_seed_manager
    if _global_seed_manager is None:
        _global_seed_manager = SeedManager(seed)
    else:
        _global_seed_manager.set_seed(seed)
    return _global_seed_manager

def get_seed_manager() -> Optional[SeedManager]:
    """
    Get the global seed manager instance.

    Returns:
        The SeedManager instance or None if not initialized.
    """
    return _global_seed_manager
