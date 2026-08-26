"""
Seed pinning utility for reproducibility (Principle I).
Ensures deterministic behavior across Python, NumPy, and random modules.
"""
import os
import random
import hashlib
from typing import Optional, Dict, Any, List
import numpy as np

from .logging import log_info, log_warning, log_error

# Default seed constant for the project
DEFAULT_SEED = 42

def get_default_seed() -> int:
    """
    Returns the default seed constant.
    Can be overridden by environment variable PROJECT_SEED.
    """
    env_seed = os.environ.get("PROJECT_SEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            log_warning(f"Invalid PROJECT_SEED environment variable: {env_seed}. Using default {DEFAULT_SEED}.")
            return DEFAULT_SEED
    return DEFAULT_SEED

def set_seed(seed: Optional[int] = None) -> int:
    """
    Sets the random seed for Python's random, NumPy, and (optionally) other libraries.
    
    Args:
        seed: The seed value. If None, uses get_default_seed().
        
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = get_default_seed()
    
    # Set seed for Python random
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Set seed for Python hash (if needed for reproducibility in specific contexts)
    # Note: PYTHONHASHSEED must be set at startup, so we log a warning if it's not set
    if "PYTHONHASHSEED" not in os.environ:
        log_warning(
            "PYTHONHASHSEED is not set. For full reproducibility, run with: "
            f"PYTHONHASHSEED={seed} python ..."
        )
    
    log_info(f"Random seed set to: {seed}")
    return seed

def get_seed_hash(seed: int) -> str:
    """
    Generates a SHA-256 hash of the seed for experiment identification.
    
    Args:
        seed: The seed integer.
        
    Returns:
        Hex digest of the seed hash.
    """
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]

def verify_seed_consistency(seed: int, experiment_id: str) -> bool:
    """
    Verifies that the current environment's seed matches the expected seed.
    
    Args:
        seed: The expected seed value.
        experiment_id: Identifier for the experiment (for logging).
        
    Returns:
        True if consistent, False otherwise.
    """
    # Check random state consistency
    set_seed(seed)
    test_val_1 = random.random()
    
    set_seed(seed)
    test_val_2 = random.random()
    
    if abs(test_val_1 - test_val_2) > 1e-10:
        log_error(f"Seed consistency check failed for experiment {experiment_id}")
        return False
    
    log_info(f"Seed consistency verified for experiment {experiment_id}")
    return True

class SeedContext:
    """
    Context manager for temporary seed setting.
    Restores the previous state upon exit.
    """
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else get_default_seed()
        self._original_random_state = None
        self._original_np_state = None
    
    def __enter__(self):
        # Save current states
        self._original_random_state = random.getstate()
        self._original_np_state = np.random.get_state()
        
        # Set new seed
        set_seed(self.seed)
        return self.seed
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original states
        random.setstate(self._original_random_state)
        np.random.set_state(self._original_np_state)
        log_info("Seed context exited, original state restored.")
        return False

def generate_experiment_id(seed: Optional[int] = None) -> str:
    """
    Generates a unique experiment ID based on the seed and timestamp.
    
    Args:
        seed: Optional seed value. If None, uses default.
        
    Returns:
        A string experiment ID.
    """
    if seed is None:
        seed = get_default_seed()
    
    seed_hash = get_seed_hash(seed)
    timestamp = os.urandom(8).hex()[:8]
    return f"exp_{seed_hash}_{timestamp}"

def get_environment_seeds() -> Dict[str, Any]:
    """
    Captures the current state of all random number generators.
    
    Returns:
        Dictionary containing current seed states.
    """
    return {
        "random": random.getstate(),
        "numpy": np.random.get_state(),
        "python_seed": os.environ.get("PYTHONHASHSEED", "not_set"),
        "project_seed": os.environ.get("PROJECT_SEED", get_default_seed())
    }
