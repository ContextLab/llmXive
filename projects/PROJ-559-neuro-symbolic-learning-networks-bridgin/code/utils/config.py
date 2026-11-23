import os
import random
import numpy as np
import torch

_global_seed = None

def set_seeds(seed: int = 42):
    """
    Sets random seeds for reproducibility across Python, NumPy, and PyTorch.
    Addresses Von Neumann's concern for stability under perturbation by ensuring
    deterministic execution given a seed.
    """
    global _global_seed
    _global_seed = seed
    
    random.seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    else:
        torch.manual_seed(seed)
    
    # Set environment variable for reproducibility in some libraries
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> Optional[int]:
    """Returns the currently set global seed."""
    return _global_seed
