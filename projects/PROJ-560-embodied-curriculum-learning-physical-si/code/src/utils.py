import random
import os
from typing import Optional
import numpy as np
import logging

def set_seed(seed: int):
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    logging.info(f"Random seed set to {seed}")
