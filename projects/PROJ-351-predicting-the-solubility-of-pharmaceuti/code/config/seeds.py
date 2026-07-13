import os
import random
import logging
from typing import Optional

import numpy as np

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default seed value for reproducibility
DEFAULT_SEED = 42

def get_seed(seed: Optional[int] = None) -> int:
    """
    Retrieve the random seed to use.
    
    Args:
        seed: Optional explicit seed value. If None, checks environment
              variable 'RANDOM_SEED', otherwise returns DEFAULT_SEED.
    
    Returns:
        The integer seed value to use for reproducibility.
    """
    if seed is not None:
        return seed
    
    env_seed = os.getenv("RANDOM_SEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            logger.warning(f"Invalid RANDOM_SEED in environment: {env_seed}. Using default.")
    
    return DEFAULT_SEED

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across Python, NumPy, and (if available) PyTorch.
    
    This function ensures that random number generation is deterministic across runs.
    It seeds:
    - Python's built-in random module
    - NumPy's random number generator
    - PyTorch (if installed) for CPU and CUDA operations
    
    Args:
        seed: Optional explicit seed value. If None, uses get_seed() to determine.
    
    Returns:
        The seed value that was set.
    """
    seed = get_seed(seed)
    
    # Seed Python's random module
    random.seed(seed)
    
    # Seed NumPy
    np.random.seed(seed)
    
    # Seed PyTorch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        logger.info(f"PyTorch seeded with {seed} (CUDA available: {torch.cuda.is_available()})")
    except ImportError:
        logger.info("PyTorch not found. Skipping PyTorch seeding.")
    
    logger.info(f"All random seeds set to {seed}")
    return seed

def ensure_seeded(seed: Optional[int] = None) -> int:
    """
    Ensure the environment is seeded for reproducibility.
    
    This is a convenience wrapper around set_seed() that guarantees
    the seed is set before any random operations occur.
    
    Args:
        seed: Optional explicit seed value.
    
    Returns:
        The seed value that was set.
    """
    return set_seed(seed)
