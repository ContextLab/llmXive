"""
Deterministic random seed management for reproducible experiments.
"""
import os
import random
import numpy as np
import torch
from typing import Optional

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.
    
    Args:
        seed: The random seed integer to use.
    """
    # Python standard library
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Environment variable for deterministic behavior
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed_value(seed: Optional[int] = None) -> int:
    """
    Get or generate a seed value.
    
    Args:
        seed: Optional explicit seed. If None, generates a random one.
        
    Returns:
        The seed integer to be used.
    """
    if seed is not None:
        return seed
    return random.randint(1000, 9999)