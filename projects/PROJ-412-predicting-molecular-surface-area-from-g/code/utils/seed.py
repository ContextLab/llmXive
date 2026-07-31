import os
import random
import hashlib
from typing import Optional, Dict, Any
import numpy as np
from .logging import get_logger

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).
    
    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed_from_env(env_var: str = "RANDOM_SEED", default: int = 42) -> int:
    """
    Get random seed from environment variable.
    
    Args:
        env_var: Environment variable name.
        default: Default seed if env var not set.
        
    Returns:
        Seed value.
    """
    seed_str = os.getenv(env_var)
    if seed_str is None:
        return default
    try:
        return int(seed_str)
    except ValueError:
        return default

def verify_seed_reproducibility(seed: int, test_func: callable, iterations: int = 3) -> bool:
    """
    Verify that a function produces reproducible results with a fixed seed.
    
    Args:
        seed: Seed to test.
        test_func: Function to test (must be deterministic).
        iterations: Number of times to run the test.
        
    Returns:
        True if all runs produce identical results.
    """
    set_seed(seed)
    results = [test_func() for _ in range(iterations)]
    return all(r == results[0] for r in results)

def generate_seed_hash(seed: int) -> str:
    """
    Generate a hash for a seed value for logging purposes.
    
    Args:
        seed: Seed value.
        
    Returns:
        Hex string hash.
    """
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]

class seed_context:
    """
    Context manager to temporarily set a random seed.
    """
    def __init__(self, seed: int):
        self.seed = seed
        self.original_state = None
    
    def __enter__(self):
        self.original_state = {
            'random': random.getstate(),
            'numpy': np.random.get_state()
        }
        set_seed(self.seed)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_state:
            random.setstate(self.original_state['random'])
            np.random.set_state(self.original_state['numpy'])
