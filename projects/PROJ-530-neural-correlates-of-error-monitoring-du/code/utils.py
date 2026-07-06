"""
Utility functions for the project.
Includes random seed pinning for reproducibility.
"""
import random
import os
import sys
from typing import Optional
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def set_global_seed(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility across libraries.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

def get_seed_status() -> dict:
    """
    Return the current status of random seeds.
    
    Returns:
        Dictionary containing seed status for available libraries.
    """
    status = {
        "python": random.getstate()[1][0],
        "numpy": np.random.get_state()[1][0],
        "torch": None
    }
    
    if HAS_TORCH:
        status["torch"] = torch.initial_seed() if torch.initial_seed() is not None else "Not set"
        
    return status