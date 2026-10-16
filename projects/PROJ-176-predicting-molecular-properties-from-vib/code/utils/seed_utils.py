"""
Utility functions for setting random seeds and retrieving seed information.
"""

import os
import random
from typing import Dict, Any, Optional

import numpy as np

try:
    import torch
except ImportError:
    torch = None

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across random, numpy, and torch (if available)."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    if torch is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_seed_info() -> Dict[str, int]:
    """Return a dictionary with the current seed values used."""
    # For simplicity, we return the PYTHONHASHSEED and assume same for random and numpy.
    seed_str = os.getenv("PYTHONHASHSEED", "0")
    try:
        seed = int(seed_str)
    except ValueError:
        seed = 0
    return {"seed": seed}
