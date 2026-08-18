"""
Seed pinning utility for reproducibility (Reproducibility Principle I).

This module provides functions to set and verify random seeds across
Python's random, NumPy, and other relevant libraries to ensure
reproducible experiments.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any, List
import numpy as np

from .logging import log_info, log_warning, log_error

# Default seed value for reproducibility
DEFAULT_SEED = 42

# Mapping of environment variables for seed configuration
SEED_ENV_VARS = {
    "PYTHONHASHSEED": "python_hash_seed",
    "NPY_SEED": "numpy_seed",
    "RANDOM_SEED": "random_seed",
}


def get_default_seed() -> int:
    """Return the default seed value."""
    return DEFAULT_SEED


def _hash_seed(seed: int) -> str:
    """Generate a deterministic hash for a seed value."""
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]


def set_seed(seed: Optional[int] = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.
        verbose: If True, log the seed configuration.

    Returns:
        A dictionary containing the seed values and their hashes.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Ensure seed is an integer
    try:
        seed = int(seed)
    except (ValueError, TypeError) as e:
        msg = f"Invalid seed value: {seed}. Must be an integer."
        log_error(msg)
        raise ValueError(msg) from e

    seed_info: Dict[str, Any] = {
        "seed": seed,
        "hash": _hash_seed(seed),
        "libraries": {},
    }

    # Set Python's random seed
    random.seed(seed)
    seed_info["libraries"]["random"] = seed

    # Set NumPy's random seed
    np.random.seed(seed)
    seed_info["libraries"]["numpy"] = seed

    # Set PYTHONHASHSEED for hash reproducibility (must be set before interpreter starts)
    # This is informational; actual setting happens via environment variable
    os.environ["PYTHONHASHSEED"] = str(seed)
    seed_info["libraries"]["python_hash"] = seed

    if verbose:
        log_info(f"Random seed set to {seed} (hash: {seed_info['hash']})")
        log_info(f"Libraries configured: {list(seed_info['libraries'].keys())}")

    return seed_info


def get_seed_hash(seed: Optional[int] = None) -> str:
    """
    Generate a deterministic hash for a seed value.

    Args:
        seed: The seed value to hash. If None, uses DEFAULT_SEED.

    Returns:
        A hexadecimal string representing the hash of the seed.
    """
    if seed is None:
        seed = DEFAULT_SEED
    return _hash_seed(int(seed))


def verify_seed_consistency(seed: int, actual_seeds: Dict[str, int]) -> bool:
    """
    Verify that the actual seeds match the expected seed.

    Args:
        seed: The expected seed value.
        actual_seeds: A dictionary of library names to their actual seed values.

    Returns:
        True if all actual seeds match the expected seed, False otherwise.
    """
    for lib, actual_seed in actual_seeds.items():
        if actual_seed != seed:
            msg = f"Seed mismatch for {lib}: expected {seed}, got {actual_seed}"
            log_warning(msg)
            return False

    log_info("All seeds are consistent")
    return True


class SeedContext:
    """
    Context manager for temporary seed setting.

    Ensures that seeds are reset to their previous values after the context
    exits, allowing for controlled randomness within a specific scope.

    Example:
        with SeedContext(42):
            # Code that needs reproducible randomness
            result = model.train()
        # Randomness restored to previous state
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else DEFAULT_SEED
        self._previous_seeds: Dict[str, int] = {}

    def __enter__(self) -> "SeedContext":
        # Store current seeds
        self._previous_seeds["random"] = random.getstate()
        self._previous_seeds["numpy"] = np.random.get_state()

        # Set new seeds
        set_seed(self.seed, verbose=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous seeds
        random.setstate(self._previous_seeds["random"])
        np.random.set_state(self._previous_seeds["numpy"])
        return False


def generate_experiment_id(seed: Optional[int] = None, prefix: str = "exp") -> str:
    """
    Generate a unique experiment ID based on the seed and timestamp.

    Args:
        seed: The seed value to include in the ID. If None, uses DEFAULT_SEED.
        prefix: A prefix for the experiment ID.

    Returns:
        A unique experiment ID string.
    """
    if seed is None:
        seed = DEFAULT_SEED

    seed_hash = get_seed_hash(seed)
    # Include a truncated timestamp for uniqueness across runs with same seed
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"{prefix}_{seed_hash}_{timestamp}"


def get_environment_seeds() -> Dict[str, Optional[int]]:
    """
    Check for seed values set via environment variables.

    Returns:
        A dictionary mapping library names to their seed values from environment,
        or None if not set.
    """
    result = {}
    for env_var, lib_name in SEED_ENV_VARS.items():
        value = os.getenv(env_var)
        result[lib_name] = int(value) if value is not None else None
    return result