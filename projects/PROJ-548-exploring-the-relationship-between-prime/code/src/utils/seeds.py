"""
Deterministic random seed management for the Prime Gap study.

This module ensures that all random number generation (Monte Carlo,
shuffling, sampling) is reproducible by enforcing a global seed
defined in `config.py`.
"""
import hashlib
import os
from typing import Optional, Dict, Any, Generator
import numpy as np
import random

from .config import get_global_seed, GLOBAL_SEED

class SeedManager:
    """
    Manages the global seed state and provides deterministic RNG instances.
    """
    _master_seed: Optional[int] = None
    _initialized: bool = False

    @classmethod
    def init(cls, seed: Optional[int] = None):
        """
        Initialize the seed manager with a specific seed or the global default.
        """
        if seed is not None:
            cls._master_seed = seed
        else:
            cls._master_seed = get_global_seed()
        cls._initialized = True

        # Set seeds for global random modules immediately
        random.seed(cls._master_seed)
        np.random.seed(cls._master_seed)

    @classmethod
    def get_master_seed(cls) -> int:
        """
        Returns the current master seed. Initializes if not set.
        """
        if not cls._initialized:
            cls.init()
        return cls._master_seed

    @classmethod
    def generate_component_seed(cls, component_name: str) -> int:
        """
        Generates a deterministic sub-seed for a specific component based on
        the master seed and the component name.
        This ensures that different parts of the pipeline can have independent
        but reproducible random streams.
        """
        master = cls.get_master_seed()
        seed_string = f"{master}:{component_name}"
        # Use SHA256 to generate a large integer, then mod 2^32
        hash_val = hashlib.sha256(seed_string.encode('utf-8')).hexdigest()
        return int(hash_val[:8], 16)

    @classmethod
    def get_rng(cls, component_name: str) -> np.random.Generator:
        """
        Returns a new numpy Generator instance seeded deterministically for
        the given component.
        """
        sub_seed = cls.generate_component_seed(component_name)
        return np.random.default_rng(sub_seed)

def set_global_seed():
    """
    Convenience function to initialize the SeedManager with the global config seed.
    Must be called before any random operations in the pipeline.
    """
    SeedManager.init()

def get_master_seed() -> int:
    """
    Returns the master seed, initializing if necessary.
    """
    return SeedManager.get_master_seed()

def generate_component_seed(component_name: str) -> int:
    """
    Generates a component-specific seed.
    """
    return SeedManager.generate_component_seed(component_name)

def get_rng(component_name: str) -> np.random.Generator:
    """
    Gets a component-specific RNG.
    """
    return SeedManager.get_rng(component_name)

def init_simulation_seed():
    """
    Alias for set_global_seed to maintain API consistency with older code.
    """
    set_global_seed()
