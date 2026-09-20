import random
import os
from typing import Optional
import numpy as np
import logging


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility across numpy, python, and os.
    
    Args:
        seed: The seed value. If None, a random seed is generated.
        
    Returns:
        The seed value used.
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    logging.info(f"Random seed set to: {seed}")
    return seed
