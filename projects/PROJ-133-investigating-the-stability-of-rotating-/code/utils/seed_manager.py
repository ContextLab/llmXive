"""
Deterministic random seed management utility for reproducible simulations.

This module provides a centralized way to manage random seeds across the
simulation pipeline, ensuring that results are reproducible when the same
seed is used, while also allowing for controlled randomness when needed.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any

import numpy as np

# Default seed if none is provided
DEFAULT_SEED = 42

# Environment variable name for setting the global seed
GLOBAL_SEED_ENV_VAR = "LLMXIVE_RANDOM_SEED"


def get_global_seed() -> int:
    """
    Retrieve the global random seed from environment or return default.

    Returns:
        int: The seed value to use for random number generation.
    """
    seed_str = os.environ.get(GLOBAL_SEED_ENV_VAR)
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            # If the environment variable is not a valid integer, fall back to default
            return DEFAULT_SEED
    return DEFAULT_SEED


def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set the global random seed in the environment.

    Args:
        seed (Optional[int]): The seed value. If None, uses the default.
    """
    if seed is None:
        seed = DEFAULT_SEED
    os.environ[GLOBAL_SEED_ENV_VAR] = str(seed)


def initialize_random_state(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize all random number generators with the given seed.

    This function ensures that Python's built-in random module, NumPy,
    and any other relevant RNGs are seeded consistently.

    Args:
        seed (Optional[int]): The seed value. If None, retrieves from
                              environment or uses default.

    Returns:
        Dict[str, Any]: A dictionary containing the initialized seed
                        and references to the seeded RNGs.
    """
    if seed is None:
        seed = get_global_seed()

    # Seed Python's random module
    random.seed(seed)

    # Seed NumPy's random generator
    np.random.seed(seed)

    return {
        "seed": seed,
        "python_random": random,
        "numpy_random": np.random,
    }


def derive_seed(base_seed: int, context: str) -> int:
    """
    Derive a deterministic sub-seed from a base seed and context string.

    This is useful for generating different but reproducible random
    sequences for different parts of a simulation while maintaining
    overall reproducibility.

    Args:
        base_seed (int): The base seed value.
        context (str): A string describing the context (e.g., "initial_conditions", "noise").

    Returns:
        int: A derived seed value in the valid range for random number generators.
    """
    # Create a hash of the base seed and context
    hash_input = f"{base_seed}:{context}".encode('utf-8')
    hash_digest = hashlib.sha256(hash_input).hexdigest()
    # Convert the first 8 hex characters to an integer
    derived_seed = int(hash_digest[:8], 16)
    return derived_seed


def get_seed_info() -> Dict[str, Any]:
    """
    Get information about the current random seed state.

    Returns:
        Dict[str, Any]: A dictionary containing seed information for logging.
    """
    current_seed = get_global_seed()
    return {
        "global_seed": current_seed,
        "env_var": GLOBAL_SEED_ENV_VAR,
        "env_value": os.environ.get(GLOBAL_SEED_ENV_VAR, "not set"),
    }


# Convenience function for scripts that need to ensure reproducibility
def ensure_reproducibility(seed: Optional[int] = None) -> None:
    """
    Ensure all random number generators are seeded for reproducibility.

    This is a convenience function for use at the start of scripts that
    require deterministic behavior.

    Args:
        seed (Optional[int]): The seed value. If None, retrieves from
                              environment or uses default.
    """
    if seed is None:
        seed = get_global_seed()
    initialize_random_state(seed)