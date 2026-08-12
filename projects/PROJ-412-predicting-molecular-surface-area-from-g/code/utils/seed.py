"""
Seed pinning utility for reproducibility.

This module provides functions to set and manage random seeds across
Python's random, NumPy, and PyTorch libraries to ensure reproducible
experiments.
"""
import os
import random
import hashlib
from typing import Optional, Dict, Any, Callable, List

import numpy as np

from .logging import get_logger

logger = get_logger(__name__)

# Default seed if none is provided
DEFAULT_SEED = 42

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all libraries.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set PyTorch's random seed (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        logger.warning("PyTorch not available, skipping PyTorch seed setting")

    # Set environment variables for reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)

    logger.info(f"Seed set to {seed} for reproducibility")
    return seed

def get_seed_from_env(env_var: str = "SEED", default: Optional[int] = None) -> int:
    """
    Retrieve seed value from environment variable.

    Args:
        env_var: Name of the environment variable to check.
        default: Default seed value if environment variable is not set.

    Returns:
        The seed value from environment or default.
    """
    seed_str = os.environ.get(env_var)
    if seed_str is not None:
        try:
            seed = int(seed_str)
            logger.info(f"Seed {seed} loaded from environment variable {env_var}")
            return seed
        except ValueError:
            logger.warning(f"Invalid seed value '{seed_str}' in {env_var}, using default")

    if default is not None:
        return default

    return DEFAULT_SEED

def verify_seed_reproducibility(
    seed: int,
    test_function: Callable[[], Dict[str, Any]],
    iterations: int = 3
) -> bool:
    """
    Verify that a given seed produces reproducible results.

    Args:
        seed: The seed to test.
        test_function: A function that returns a dictionary of results.
        iterations: Number of times to run the test.

    Returns:
        True if all iterations produce identical results, False otherwise.
    """
    results: List[Dict[str, Any]] = []

    for i in range(iterations):
        set_seed(seed)
        result = test_function()
        results.append(result)

    # Compare all results to the first one
    first_result = results[0]
    for i, result in enumerate(results[1:], start=2):
        if result != first_result:
            logger.error(f"Seed {seed} failed reproducibility check at iteration {i}")
            return False

    logger.info(f"Seed {seed} passed reproducibility check over {iterations} iterations")
    return True

def generate_seed_hash(seed: int, additional_data: Optional[str] = None) -> str:
    """
    Generate a unique hash for a seed and optional additional data.

    Args:
        seed: The seed value.
        additional_data: Optional string data to include in the hash.

    Returns:
        A SHA-256 hash string.
    """
    hash_input = str(seed)
    if additional_data:
        hash_input += f":{additional_data}"

    return hashlib.sha256(hash_input.encode()).hexdigest()

class seed_context:
    """
    Context manager for temporary seed setting.

    Usage:
        with seed_context(123):
            # Code that needs reproducible randomness
            pass
        # Seed is restored to previous state
    """

    def __init__(self, seed: int):
        self.seed = seed
        self.previous_seed: Optional[int] = None

    def __enter__(self):
        # Save current seed state (simplified - in practice, would need to track more state)
        self.previous_seed = int(os.environ.get('PYTHONHASHSEED', -1))
        set_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous seed state
        if self.previous_seed != -1:
            set_seed(self.previous_seed)
        return False

def get_seed_info() -> Dict[str, Any]:
    """
    Get information about the current seed configuration.

    Returns:
        Dictionary with seed information.
    """
    seed = get_seed_from_env()
    return {
        "seed": seed,
        "hash": generate_seed_hash(seed),
        "environment_source": os.environ.get("SEED", "not_set"),
        "python_hash_seed": os.environ.get('PYTHONHASHSEED', 'not_set')
    }

if __name__ == "__main__":
    # Simple test when run directly
    print("Testing seed pinning...")
    seed = get_seed_from_env()
    set_seed(seed)

    # Test basic randomness
    print(f"Random int: {random.randint(0, 100)}")
    print(f"Numpy random: {np.random.random()}")

    info = get_seed_info()
    print(f"Seed info: {info}")

    # Verify reproducibility
    def simple_test():
        return {
            "rand": random.randint(0, 1000),
            "np_rand": float(np.random.random())
        }

    is_reproducible = verify_seed_reproducibility(seed, simple_test, 3)
    print(f"Reproducibility test: {'PASSED' if is_reproducible else 'FAILED'}")