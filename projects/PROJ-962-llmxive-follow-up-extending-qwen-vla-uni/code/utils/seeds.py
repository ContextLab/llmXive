import random
import os
from typing import Optional, List, Union, Any
import numpy as np

_global_seed: Optional[int] = None

def set_global_seed(seed: Optional[int] = 42) -> None:
    """
    Set the global random seed for reproducibility across all libraries.
    
    Args:
        seed: The seed value to set. If None, uses a default (42).
    """
    global _global_seed
    _global_seed = seed if seed is not None else 42
    
    random.seed(_global_seed)
    os.environ["PYTHONHASHSEED"] = str(_global_seed)
    np.random.seed(_global_seed)
    
    try:
        import torch
        torch.manual_seed(_global_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(_global_seed)
            torch.cuda.manual_seed_all(_global_seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

def get_seed() -> Optional[int]:
    """
    Get the current global seed value.
    
    Returns:
        The current seed value, or None if not set.
    """
    return _global_seed

def reset_seed() -> None:
    """
    Reset the global seed to None (uninitialized state).
    """
    global _global_seed
    _global_seed = None
