import random
import os
from typing import Optional

def set_global_seed(seed: int = 42) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    """
    Get the current global seed.
    
    Returns:
        The seed value.
    """
    return int(os.environ.get('PYTHONHASHSEED', 42))
