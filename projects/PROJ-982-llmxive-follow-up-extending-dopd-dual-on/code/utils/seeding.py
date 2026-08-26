"""
Deterministic random state management for reproducible experiments.

This module provides a unified interface to seed all random number generators
used in the project (Python stdlib, NumPy, and optionally PyTorch/TensorFlow
if installed) to ensure bitwise reproducibility across runs.
"""

import random
import hashlib
import os
from typing import Optional, Dict, Any, List

import numpy as np

# Optional deep learning imports - fail gracefully if not present
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


def derive_seed_from_string(seed_string: str, max_value: int = 2**32 - 1) -> int:
    """
    Derive a deterministic integer seed from a string input.

    Args:
        seed_string: The input string to hash.
        max_value: Maximum allowed value for the seed (default: 2^32 - 1).

    Returns:
        A deterministic integer seed in the range [0, max_value].
    """
    if not isinstance(seed_string, str):
        raise TypeError("seed_string must be a string")

    # Use SHA-256 for robust hashing
    hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
    hash_bytes = hash_obj.digest()

    # Convert first 4 bytes to an integer
    seed_int = int.from_bytes(hash_bytes[:4], byteorder='big')

    return seed_int % (max_value + 1)


def deterministic_seed(seed: int) -> None:
    """
    Set seeds for all random number generators to a specific integer.

    This ensures full reproducibility by seeding:
    - Python's random module
    - NumPy's random generator
    - PyTorch (if available)
    - TensorFlow (if available)

    Args:
        seed: The integer seed value.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)}")

    # Seed Python standard library
    random.seed(seed)

    # Seed NumPy
    np.random.seed(seed)

    # Seed PyTorch if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Seed TensorFlow if available
    if TF_AVAILABLE:
        tf.random.set_seed(seed)


def seed_everything(seed: Optional[int] = None) -> int:
    """
    Initialize random seeds for the entire experiment.

    If a seed is provided, it is used directly. If None, a seed is derived
    from the environment variable `EXPERIMENT_SEED` or defaults to 42.

    Args:
        seed: Optional explicit seed value.

    Returns:
        The seed value that was used.
    """
    if seed is None:
        env_seed = os.getenv("EXPERIMENT_SEED")
        if env_seed is not None:
            try:
                seed = int(env_seed)
            except ValueError:
                # If env var is not an int, derive from it
                seed = derive_seed_from_string(env_seed)
        else:
            seed = 42

    deterministic_seed(seed)
    return seed


def get_rng_state() -> Dict[str, Any]:
    """
    Capture the current state of all random number generators.

    Returns:
        A dictionary containing the state of Python random, NumPy,
        and PyTorch/TensorFlow RNGs (if available).
    """
    state = {
        "python_random": random.getstate(),
        "numpy": np.random.get_state(),
    }

    if TORCH_AVAILABLE:
        state["torch_cpu"] = torch.get_rng_state()
        if torch.cuda.is_available():
            state["torch_cuda"] = torch.cuda.get_rng_state_all()

    if TF_AVAILABLE:
        # TensorFlow 2.x global state
        state["tensorflow"] = tf.random.get_global_generator().experimental_state

    return state


def set_rng_state(state: Dict[str, Any]) -> None:
    """
    Restore the state of all random number generators.

    Args:
        state: The dictionary returned by `get_rng_state()`.
    """
    random.setstate(state["python_random"])
    np.random.set_state(state["numpy"])

    if TORCH_AVAILABLE:
        torch.set_rng_state(state["torch_cpu"])
        if "torch_cuda" in state and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(state["torch_cuda"])

    if TF_AVAILABLE and "tensorflow" in state:
        # TensorFlow 2.x global state restoration
        tf.random.set_global_generator(
            tf.random.experimental.Generator.from_state(state["tensorflow"])
        )


def generate_seed_sequence(base_seed: int, count: int) -> List[int]:
    """
    Generate a sequence of deterministic seeds derived from a base seed.

    This is useful for creating independent but reproducible seeds for
    parallel experiments or multiple runs.

    Args:
        base_seed: The base integer seed.
        count: Number of seeds to generate.

    Returns:
        A list of `count` unique integer seeds.
    """
    if count <= 0:
        raise ValueError("count must be positive")

    seeds = []
    current_seed = base_seed
    for i in range(count):
        # Derive next seed from current seed string representation
        seed_str = f"{base_seed}_{i}"
        derived = derive_seed_from_string(seed_str)
        seeds.append(derived)

    return seeds