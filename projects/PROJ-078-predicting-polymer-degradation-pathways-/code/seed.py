"""
Seed management module for deterministic reproducibility.
Centralizes random seed initialization across numpy, random, and torch.
"""
import os
import random
import numpy as np

def set_seed(seed: int = 42):
    """
    Set random seed for reproducibility across all libraries.
    
    Args:
        seed: Random seed value (default: 42)
    """
    # Python's random module
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # Python hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass