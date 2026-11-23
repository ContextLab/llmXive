import hashlib
import os
from typing import Optional, Dict, Any, Generator
import numpy as np
import random

# Import GLOBAL_SEED from config to ensure single source of truth
from .config import get_global_seed, GLOBAL_SEED

class SeedManager:
    """
    Manages deterministic random seed generation for reproducibility.
    Ensures all random generators use the GLOBAL_SEED defined in config.py.
    """

    _master_seed: Optional[int] = None

    @classmethod
    def set_master_seed(cls, seed: Optional[int] = None) -> int:
        """
        Set the master seed for the entire simulation.
        If seed is None, uses GLOBAL_SEED from config.
        Returns the seed used.
        """
        if seed is None:
            seed = get_global_seed()
        cls._master_seed = seed
        return seed

    @classmethod
    def get_master_seed(cls) -> int:
        """Returns the current master seed, initializing if necessary."""
        if cls._master_seed is None:
            cls.set_master_seed()
        return cls._master_seed

    @classmethod
    def generate_component_seed(cls, component_name: str) -> int:
        """
        Generates a deterministic seed for a specific component based on the master seed.
        This ensures reproducibility while allowing distinct seeds per module.
        """
        master = cls.get_master_seed()
        # Hash the component name with the master seed to get a unique but deterministic seed
        hash_input = f"{master}:{component_name}".encode('utf-8')
        hash_val = hashlib.sha256(hash_input).hexdigest()
        # Convert first 8 hex chars to int
        return int(hash_val[:8], 16)

def set_global_seed(seed: Optional[int] = None) -> int:
    """Convenience function to set the master seed."""
    return SeedManager.set_master_seed(seed)

def get_master_seed() -> int:
    """Convenience function to get the master seed."""
    return SeedManager.get_master_seed()

def generate_component_seed(component_name: str) -> int:
    """Convenience function to generate a component-specific seed."""
    return SeedManager.generate_component_seed(component_name)

def get_rng(component_name: Optional[str] = None, seed: Optional[int] = None):
    """
    Returns a new numpy.random.Generator instance initialized with the correct seed.
    If component_name is provided, derives a seed from the master seed.
    If explicit seed is provided, uses that.
    """
    if seed is None:
        if component_name:
            seed = generate_component_seed(component_name)
        else:
            seed = get_master_seed()
    return np.random.default_rng(seed)

def init_simulation_seed():
    """
    Initializes the global Python random and numpy random states with the master seed.
    This should be called once at the entry point of any script to ensure full reproducibility.
    """
    seed = get_master_seed()
    random.seed(seed)
    np.random.seed(seed)
    # Also set the global master seed in the manager
    SeedManager.set_master_seed(seed)
    return seed
