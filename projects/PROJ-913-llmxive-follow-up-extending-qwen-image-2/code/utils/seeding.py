import os
import random
from typing import Optional
import numpy as np
from config import SEED

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Sets global random seeds for reproducibility.
    """
    if seed is None:
        seed = SEED
    
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    
    # If torch is available, set its seed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed_context(seed: Optional[int] = None):
    """
    Returns a context manager or seed value for specific operations.
    """
    if seed is None:
        return SEED
    return seed
