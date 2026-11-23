"""
Deterministic seed management for the prime gap analysis pipeline.

This module provides utilities for managing random seeds to ensure
reproducibility across all random operations in the pipeline.
"""
import hashlib
import os
from typing import Optional, Dict, Any, Generator
import numpy as np
import random
from .config import get_global_seed, GLOBAL_SEED


class SeedManager:
    """
    Manages deterministic random seed generation for various components.

    This class ensures that all random number generators in the pipeline
    are initialized with deterministic seeds derived from a master seed,
    enabling full reproducibility of results.
    """

    def __init__(self, master_seed: Optional[int] = None):
        """
        Initialize the SeedManager.

        Args:
            master_seed: The master seed value. If None, uses GLOBAL_SEED from config.
        """
        self.master_seed = master_seed if master_seed is not None else get_global_seed()
        self._component_seeds: Dict[str, int] = {}

    def get_master_seed(self) -> int:
        """Return the master seed value."""
        return self.master_seed

    def generate_component_seed(self, component_name: str) -> int:
        """
        Generate a deterministic seed for a specific component.

        Args:
            component_name: Unique identifier for the component.

        Returns:
            int: A deterministic seed derived from the master seed and component name.
        """
        if component_name in self._component_seeds:
            return self._component_seeds[component_name]

        # Create a deterministic seed by hashing the master seed and component name
        seed_string = f"{self.master_seed}:{component_name}"
        hash_obj = hashlib.sha256(seed_string.encode())
        seed_value = int(hash_obj.hexdigest(), 16) % (2**32)

        self._component_seeds[component_name] = seed_value
        return seed_value

    def get_rng(self, component_name: str, rng_type: str = "numpy") -> Any:
        """
        Get a random number generator for a specific component.

        Args:
            component_name: Unique identifier for the component.
            rng_type: Type of RNG ("numpy" or "random").

        Returns:
            An initialized random number generator.
        """
        seed = self.generate_component_seed(component_name)

        if rng_type == "numpy":
            return np.random.default_rng(seed)
        elif rng_type == "random":
            random.seed(seed)
            return random
        else:
            raise ValueError(f"Unsupported RNG type: {rng_type}")


def set_global_seed(seed: int):
    """
    Set the global seed for the entire pipeline.

    Note: This updates the GLOBAL_SEED in the config module.
    """
    global GLOBAL_SEED
    GLOBAL_SEED = seed
    # Update the config module's GLOBAL_SEED as well
    import sys
    if 'src.utils.config' in sys.modules:
        sys.modules['src.utils.config'].GLOBAL_SEED = seed


def get_master_seed() -> int:
    """
    Get the current master seed.

    Returns:
        int: The current GLOBAL_SEED value.
    """
    return get_global_seed()


def generate_component_seed(component_name: str, master_seed: Optional[int] = None) -> int:
    """
    Generate a deterministic seed for a specific component.

    Args:
        component_name: Unique identifier for the component.
        master_seed: Optional master seed. If None, uses GLOBAL_SEED.

    Returns:
        int: A deterministic seed derived from the master seed and component name.
    """
    seed_manager = SeedManager(master_seed)
    return seed_manager.generate_component_seed(component_name)


def get_rng(component_name: str, rng_type: str = "numpy", master_seed: Optional[int] = None) -> Any:
    """
    Get a random number generator for a specific component.

    Args:
        component_name: Unique identifier for the component.
        rng_type: Type of RNG ("numpy" or "random").
        master_seed: Optional master seed. If None, uses GLOBAL_SEED.

    Returns:
        An initialized random number generator.
    """
    seed_manager = SeedManager(master_seed)
    return seed_manager.get_rng(component_name, rng_type)


def init_simulation_seed(component_name: str, master_seed: Optional[int] = None):
    """
    Initialize all random number generators for a simulation component.

    This function ensures both numpy and Python's random module are seeded
    consistently for a given component.

    Args:
        component_name: Unique identifier for the component.
        master_seed: Optional master seed. If None, uses GLOBAL_SEED.
    """
    seed_manager = SeedManager(master_seed)
    # Initialize numpy RNG
    seed_manager.get_rng(component_name, "numpy")
    # Initialize Python random
    seed_manager.get_rng(component_name, "random")
