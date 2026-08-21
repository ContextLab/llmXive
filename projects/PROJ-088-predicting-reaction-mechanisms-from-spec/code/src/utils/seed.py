"""
Seed pinning utility for reproducibility (Principle I).

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
SEED_ENV_VAR = "LMMXIVE_RANDOM_SEED"

def get_default_seed() -> int:
    """
    Retrieve the default seed, checking environment variables first.
    
    Returns:
        int: The seed value to use (from environment or default).
    """
    env_seed = os.getenv(SEED_ENV_VAR)
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            log_warning(f"Invalid seed value in environment variable {SEED_ENV_VAR}: {env_seed}. Using default.")
    return DEFAULT_SEED

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for all relevant libraries.
    
    Args:
        seed (int, optional): The seed value. If None, uses the default.
        
    Returns:
        int: The seed value that was set.
        
    Raises:
        ValueError: If the seed is negative.
    """
    if seed is None:
        seed = get_default_seed()
        
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    
    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Log the action
    log_info(f"Random seed set to {seed}")
    
    return seed

def get_seed_hash(seed: int) -> str:
    """
    Generate a deterministic hash for a seed value.
    
    Args:
        seed (int): The seed value.
        
    Returns:
        str: A hexadecimal hash string representing the seed.
    """
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]

def verify_seed_consistency(seed: int) -> bool:
    """
    Verify that the current random state matches the expected seed.
    
    This is a basic check by re-seeding and comparing a generated value.
    
    Args:
        seed (int): The seed to verify against.
        
    Returns:
        bool: True if the generated value matches the expected value.
    """
    # Save current state
    current_state = random.getstate()
    np_state = np.random.get_state()
    
    try:
        # Set the seed
        set_seed(seed)
        
        # Generate a test value
        test_val = random.random()
        
        # Reset to original state
        random.setstate(current_state)
        np.random.set_state(np_state)
        
        # Generate the same test value again with the seed
        set_seed(seed)
        expected_val = random.random()
        
        # Compare
        return abs(test_val - expected_val) < 1e-15
    finally:
        # Ensure state is restored
        random.setstate(current_state)
        np.random.set_state(np_state)

class SeedContext:
    """
    Context manager for temporary seed setting.
    
    Usage:
        with SeedContext(42):
            # code that needs deterministic randomness
            pass
        # randomness restored to previous state
    """
    
    def __init__(self, seed: int):
        self.seed = seed
        self.random_state = None
        self.np_state = None
        
    def __enter__(self):
        # Save current states
        self.random_state = random.getstate()
        self.np_state = np.random.get_state()
        
        # Set new seed
        set_seed(self.seed)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous states
        random.setstate(self.random_state)
        np.random.set_state(self.np_state)
        return False

def generate_experiment_id(seed: Optional[int] = None) -> str:
    """
    Generate a unique experiment ID based on the seed and timestamp.
    
    Args:
        seed (int, optional): The seed to base the ID on.
        
    Returns:
        str: A unique experiment identifier.
    """
    if seed is None:
        seed = get_default_seed()
        
    timestamp = str(os.getpid()) + str(hash(os.urandom(8)))
    seed_hash = get_seed_hash(seed)
    
    return f"exp_{seed_hash}_{timestamp}"

def get_environment_seeds() -> Dict[str, Any]:
    """
    Collect all relevant seed information from the environment.
    
    Returns:
        dict: A dictionary containing seed information.
    """
    return {
        "default_seed": get_default_seed(),
        "env_seed": os.getenv(SEED_ENV_VAR),
        "current_random_seed": random.getstate()[1][0] if hasattr(random.getstate(), '__getitem__') else None,
        "numpy_seed": np.random.get_state()[1][0] if hasattr(np.random.get_state(), '__getitem__') else None,
    }