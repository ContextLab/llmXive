import os
import random
import sys
from typing import Optional, Union
import numpy as np

def validate_seed(seed: int) -> bool:
    """Validate that the seed is a non-negative integer."""
    return isinstance(seed, int) and seed >= 0

def set_deterministic_seed(seed: int = 42) -> None:
    """Set deterministic seeds for reproducibility."""
    if not validate_seed(seed):
        raise ValueError(f"Invalid seed: {seed}. Must be a non-negative integer.")
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # If CUDA is available, set seeds for PyTorch/TensorFlow if imported
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed_context(seed: int = 42) -> dict:
    """Return a context dictionary with the seed and status."""
    return {
        "seed": seed,
        "is_deterministic": True,
        "environment_hash": os.environ.get('PYTHONHASHSEED', 'not_set')
    }

def is_deterministic_configured() -> bool:
    """Check if deterministic mode is configured."""
    return os.environ.get('PYTHONHASHSEED') is not None
