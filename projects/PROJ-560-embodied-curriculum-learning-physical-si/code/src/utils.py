import random
import os
from typing import Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: The seed value. If None, a default seed (42) is used.
        
    Returns:
        The seed value used.
    """
    if seed is None:
        seed = 42
    
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    
    logger.info(f"Random seed set to {seed}")
    return seed