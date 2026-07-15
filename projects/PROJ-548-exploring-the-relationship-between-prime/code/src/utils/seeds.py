"""
Deterministic random seed management for Monte Carlo and simulation tasks.

This module provides a centralized, reproducible seed management system ensuring
that all stochastic operations in the pipeline (Monte Carlo simulations,
random sampling, etc.) are fully deterministic and reproducible given a master seed.

It supports:
  - Master seed derivation from a config file or environment variable.
  - Component-specific seed generation (e.g., 'cramer', 'permutation') via hashing.
  - Global numpy random state locking.
  - RNG factory for creating isolated, reproducible generators.
"""
import hashlib
import os
from typing import Optional, Dict, Any, Generator
import numpy as np

# Default master seed if none is provided
DEFAULT_MASTER_SEED = 42
SEED_CONFIG_ENV_VAR = "LLMXIVE_MASTER_SEED"


class SeedManager:
    """
    Manages the global seed state and provides deterministic child seeds.

    This class ensures that once a master seed is set, all subsequent random
    operations in the pipeline are reproducible. It handles the derivation of
    component-specific seeds to ensure independence between different stochastic
    processes while maintaining overall determinism.
    """

    _master_seed: Optional[int] = None
    _global_rng: Optional[np.random.Generator] = None

    @classmethod
    def set_master_seed(cls, seed: int) -> None:
        """
        Sets the global master seed for the entire pipeline.

        Args:
            seed: An integer seed value.
        """
        cls._master_seed = seed
        cls._global_rng = np.random.default_rng(seed)
        # Also set legacy global state for compatibility if needed, though
        # modern numpy usage should rely on the Generator instance.
        np.random.seed(seed)

    @classmethod
    def get_master_seed(cls) -> int:
        """
        Retrieves the current master seed.

        Returns:
            The master seed integer. Defaults to DEFAULT_MASTER_SEED if not set.
        """
        if cls._master_seed is None:
            # Try environment variable first, then default
            env_seed = os.getenv(SEED_CONFIG_ENV_VAR)
            if env_seed is not None:
                cls._master_seed = int(env_seed)
            else:
                cls._master_seed = DEFAULT_MASTER_SEED
        return cls._master_seed

    @classmethod
    def generate_component_seed(cls, component_name: str, salt: str = "") -> int:
        """
        Generates a deterministic seed for a specific component based on the master seed.

        This ensures that 'cramer_simulation' always gets the same seed derived from
        the master seed, while 'permutation_test' gets a different one, but both
        are reproducible.

        Args:
            component_name: A string identifying the component (e.g., 'monte_carlo').
            salt: An optional additional string to further differentiate seeds.

        Returns:
            A 32-bit integer seed derived deterministically.
        """
        master = cls.get_master_seed()
        # Create a deterministic string for hashing
        seed_string = f"{master}:{component_name}:{salt}"
        # Hash using SHA256 and take the first 8 bytes (64 bits), then mod 2^32
        hash_digest = hashlib.sha256(seed_string.encode('utf-8')).digest()
        seed_int = int.from_bytes(hash_digest[:8], byteorder='big') % (2**32)
        return seed_int

    @classmethod
    def get_rng(cls, component_name: str, salt: str = "") -> np.random.Generator:
        """
        Returns a dedicated numpy Generator for a specific component.

        This is the preferred way to obtain randomness in the pipeline to ensure
        isolation and reproducibility.

        Args:
            component_name: The name of the component requesting the RNG.
            salt: Optional salt for further differentiation.

        Returns:
            A numpy.random.Generator instance seeded deterministically.
        """
        component_seed = cls.generate_component_seed(component_name, salt)
        return np.random.default_rng(component_seed)

    @classmethod
    def set_global_seed(cls, seed: Optional[int] = None) -> None:
        """
        Convenience wrapper to set the master seed and update global numpy state.

        Args:
            seed: Optional seed integer. If None, uses environment or default.
        """
        if seed is not None:
            cls.set_master_seed(seed)
        else:
            cls.set_master_seed(cls.get_master_seed())


def get_master_seed() -> int:
    """Convenience function to get the current master seed."""
    return SeedManager.get_master_seed()


def generate_component_seed(component_name: str, salt: str = "") -> int:
    """Convenience function to generate a component seed."""
    return SeedManager.generate_component_seed(component_name, salt)


def get_rng(component_name: str, salt: str = "") -> np.random.Generator:
    """Convenience function to get a component-specific RNG."""
    return SeedManager.get_rng(component_name, salt)


def set_global_seed(seed: Optional[int] = None) -> None:
    """Convenience function to set the global seed."""
    SeedManager.set_global_seed(seed)


def init_simulation_seed(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initializes the seed management system based on a configuration dictionary.

    This function is intended to be called at the entry point of simulation scripts
    (e.g., Monte Carlo runs) to ensure they start with the correct deterministic state.

    Args:
        config: A dictionary containing 'master_seed' key. If None, defaults are used.
    """
    if config and 'master_seed' in config:
        seed = int(config['master_seed'])
    else:
        seed = None
    set_global_seed(seed)
