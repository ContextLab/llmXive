"""
Seeding utilities for reproducible experiments.
"""
import random
import os
import numpy as np
import torch
from typing import Optional

DEFAULT_SEED = 42

def set_deterministic_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across all libraries.

    Args:
        seed: The random seed to use.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_seed_value() -> int:
    """
    Get the current seed value (returns DEFAULT_SEED if not set explicitly in a global context).
    """
    return DEFAULT_SEED
