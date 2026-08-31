"""
Configuration module for deterministic random seeds and reproducibility.

This module provides utilities to ensure that all random number generation
across the simulation pipeline is deterministic and reproducible.
"""
import os
import random
import hashlib
import numpy as np
from typing import Optional, Dict, Any, Tuple


# Global seed state to track initialization
_seed_initialized: bool = False
_current_seed: Optional[int] = None


def get_seed_from_env(default_seed: int = 42) -> int:
    """
    Retrieve the random seed from the environment variable 'LLMXIVE_SEED'.
    
    Args:
        default_seed: Default seed value if environment variable is not set.
    
    Returns:
        The seed value as an integer.
    """
    seed_str = os.environ.get("LLMXIVE_SEED")
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            raise ValueError(f"Invalid seed value in LLMXIVE_SEED: {seed_str}")
    return default_seed


def set_seed(seed: int) -> None:
    """
    Set the random seed for all relevant random number generators.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy's random number generator
    
    Args:
        seed: The integer seed value to use.
    """
    global _seed_initialized, _current_seed
    
    random.seed(seed)
    np.random.seed(seed)
    
    _seed_initialized = True
    _current_seed = seed


def initialize_reproducibility(config: Optional[Dict[str, Any]] = None) -> Tuple[int, str]:
    """
    Initialize reproducibility for the entire pipeline.
    
    This function:
    1. Reads the seed from environment or config
    2. Sets seeds for all random number generators
    3. Returns the seed and a configuration hash for tracking
    
    Args:
        config: Optional configuration dictionary. If provided, looks for
               'seed' key. Otherwise, uses environment variable.
    
    Returns:
        Tuple of (seed_value, config_hash)
    
    Raises:
        ValueError: If seed is invalid or configuration is malformed.
    """
    # Determine seed source
    if config and 'seed' in config:
        seed = config['seed']
    else:
        seed = get_seed_from_env()
    
    # Validate seed
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")
    
    # Set the seed
    set_seed(seed)
    
    # Generate a hash for tracking this configuration
    config_hash = get_config_hash(config)
    
    return seed, config_hash


def get_config_hash(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a deterministic hash of the configuration for reproducibility tracking.
    
    Args:
        config: Configuration dictionary to hash. If None, uses current seed.
    
    Returns:
        Hexadecimal string representation of the hash.
    """
    if config is None:
        # Hash the current seed if no config provided
        config = {'seed': _current_seed}
    
    # Create a deterministic string representation
    config_str = str(sorted(config.items()))
    hash_obj = hashlib.sha256(config_str.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


def is_seed_initialized() -> bool:
    """
    Check if the seed has been initialized.
    
    Returns:
        True if set_seed has been called, False otherwise.
    """
    return _seed_initialized


def get_current_seed() -> Optional[int]:
    """
    Get the currently set seed value.
    
    Returns:
        The current seed value, or None if not initialized.
    """
    return _current_seed
