"""
Utility to set deterministic seeds across common libraries.

This module provides a single public function ``set_seeds`` that seeds
Python's ``random`` module, NumPy, and (if available) PyTorch. It also
fixes the ``PYTHONHASHSEED`` environment variable to ensure reproducible
hashing of built‑in types.

The function is deliberately lightweight and has no side‑effects beyond
seeding; it can be called multiple times (the most recent call wins).
"""

import os
import random
from typing import Optional

def set_seeds(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility.

    Parameters
    ----------
    seed : int, optional
        The seed value to use. Defaults to 42.

    This function seeds:
    - ``random`` (Python's built‑in RNG)
    - ``numpy.random``
    - ``torch`` (if installed)
    - ``PYTHONHASHSEED`` environment variable
    """
    # Standard library RNG
    random.seed(seed)

    # NumPy RNG
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:  # pragma: no cover
        pass

    # PyTorch RNG (CPU‑only; ignore if torch not installed)
    try:
        import torch
        torch.manual_seed(seed)
        # Ensure deterministic behavior on CUDA if ever used
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Disable nondeterministic algorithms
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:  # pragma: no cover
        pass

    # Hash seed for reproducible hashing of built‑in types
    os.environ["PYTHONHASHSEED"] = str(seed)
