"""
Random seed management for reproducibility.
"""
import random
import os
from typing import Optional
import numpy as np

class SeedManager:
    """Manages random seeds for reproducibility."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
    
    def set_seed(self) -> None:
        """Set seeds for all random number generators."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        if os.environ.get('PYTHONHASHSEED') is None:
            os.environ['PYTHONHASHSEED'] = str(self.seed)

def set_seed(seed: int = 42) -> SeedManager:
    """
    Set global random seeds.
    
    Args:
        seed: Random seed value.
        
    Returns:
        SeedManager instance.
    """
    manager = SeedManager(seed)
    manager.set_seed()
    return manager

def get_seed_manager() -> SeedManager:
    """Get the default seed manager."""
    return set_seed(42)
