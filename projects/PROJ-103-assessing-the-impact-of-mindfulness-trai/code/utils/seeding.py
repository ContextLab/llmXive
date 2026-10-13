"""
Utility for deterministic seeding across supported scientific libraries.

The pipeline relies on reproducibility; this module pins the random state for
Python's built‑in ``random`` module, NumPy, and (optionally) PyTorch.
"""

import random
import numpy as np
from typing import Optional

def set_seed(seed: int = 42) -> None:
    """
    Set the global random seed for reproducibility.

    Parameters
    ----------
    seed : int, optional
        The seed value to use for all supported libraries. Default is 42.
    """
    # Python's standard library
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch is optional – if it is installed we also seed it.
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # PyTorch not installed; nothing to do.
        pass
