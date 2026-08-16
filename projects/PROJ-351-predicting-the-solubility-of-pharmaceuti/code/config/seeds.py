import os
import random
import logging
from typing import Optional
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_SEED = 42

def get_seed(seed: Optional[int] = None) -> int:
    """
    Get the random seed to use.
    
    Args:
        seed: Optional seed value. If None, uses DEFAULT_SEED.
        
    Returns:
        The seed value to use.
    """
    if seed is not None:
        return seed
    
    # Check environment variable
    env_seed = os.environ.get("RANDOM_SEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            logger.warning(f"Invalid seed in environment: {env_seed}, using default")
    
    return DEFAULT_SEED

def set_seed(seed: int):
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed: The seed value to set.
    """
    # Python random
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    logger.info(f"Random seed set to: {seed}")

def ensure_seeded(seed: Optional[int] = None):
    """
    Ensure all random seeds are set for reproducibility.
    
    Args:
        seed: Optional seed value. If None, uses DEFAULT_SEED.
    """
    final_seed = get_seed(seed)
    set_seed(final_seed)
    return final_seed
