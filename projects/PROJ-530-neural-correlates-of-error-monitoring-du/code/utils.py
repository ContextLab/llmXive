"""
Utility functions for the research pipeline.
Includes random seed management and other helper functions.
"""
import random
import os
import sys
from typing import Optional
import numpy as np

def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for reproducibility.

    This function sets seeds for:
    - Python's random module
    - NumPy
    - Environment variables (PYTHONHASHSEED)

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Note: If using PyTorch, you would also set:
    # import torch
    # torch.manual_seed(seed)
    # torch.cuda.manual_seed_all(seed)

def get_seed_status() -> dict:
    """
    Get the current status of random seeds.

    Returns:
        Dictionary containing current seed values for each module.
    """
    return {
        'python_random': random.getstate()[1][0],
        'numpy': np.random.get_state()[1][0],
        'python_hash_seed': os.environ.get('PYTHONHASHSEED', 'not set')
    }