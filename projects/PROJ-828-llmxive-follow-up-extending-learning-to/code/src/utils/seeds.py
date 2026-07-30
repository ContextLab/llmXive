"""
Deterministic seed pinning utilities for reproducible experiments.

This module provides functions to set and manage random seeds across
Python's random module, NumPy, and PyTorch to ensure reproducible results.
"""

import os
import random
import hashlib
import numpy as np
import torch
from typing import Optional, Dict, Any, Union


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across all relevant libraries.

    Args:
        seed: Integer seed value to use for random number generation.
    """
    # Set Python random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch random seeds
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # If using multi-GPU

    # Set environment variables for determinism
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Configure PyTorch for deterministic behavior
    torch.use_deterministic_algorithms(True)
    # Note: This may require setting os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    # for CUDA operations to be fully deterministic


def generate_seed_from_string(seed_string: str, max_seed: int = 2**32 - 1) -> int:
    """
    Generate a deterministic integer seed from a string.

    Args:
        seed_string: Input string to hash.
        max_seed: Maximum value for the generated seed (default: 2^32 - 1).

    Returns:
        Integer seed value derived from the input string.
    """
    # Hash the string using SHA-256
    hash_object = hashlib.sha256(seed_string.encode('utf-8'))
    hash_bytes = hash_object.digest()

    # Convert first 4 bytes to an integer
    seed_int = int.from_bytes(hash_bytes[:4], byteorder='big')

    # Ensure it's within the valid range
    return seed_int % (max_seed + 1)


def get_seed_config(seed: Optional[int] = None, seed_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a configuration dictionary for seed management.

    Args:
        seed: Direct seed value (optional).
        seed_string: String to derive seed from (optional).

    Returns:
        Dictionary containing seed configuration information.
    """
    if seed is not None:
        final_seed = seed
    elif seed_string is not None:
        final_seed = generate_seed_from_string(seed_string)
    else:
        # Default to a fixed seed if neither is provided
        final_seed = 42

    return {
        'seed': final_seed,
        'seed_string': seed_string,
        'is_deterministic': True,
        'environment_seed': os.environ.get('PYTHONHASHSEED', None)
    }


def apply_seed_config(config: Dict[str, Any]) -> int:
    """
    Apply a seed configuration dictionary to set all random seeds.

    Args:
        config: Dictionary containing seed configuration (must have 'seed' key).

    Returns:
        The seed value that was applied.
    """
    seed = config.get('seed')
    if seed is None:
        raise ValueError("Seed configuration must contain a 'seed' key")

    set_seed(seed)
    return seed


def get_seed_environment() -> Dict[str, str]:
    """
    Get the current seed-related environment variables.

    Returns:
        Dictionary of environment variables related to seeding.
    """
    return {
        'PYTHONHASHSEED': os.environ.get('PYTHONHASHSEED', 'not_set'),
        'CUBLAS_WORKSPACE_CONFIG': os.environ.get('CUBLAS_WORKSPACE_CONFIG', 'not_set'),
        'CUDA_DETERMINISTIC': os.environ.get('CUDA_DETERMINISTIC', 'not_set')
    }
