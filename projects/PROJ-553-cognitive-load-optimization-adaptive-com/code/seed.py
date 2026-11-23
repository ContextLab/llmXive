"""
Seed module for reproducible experiments.

This module defines a constant SEED and provides a helper function
`set_seed()` that sets the random seed for the following libraries:

- Python's built-in `random`
- NumPy's random generator
- PyTorch (if installed)

Importing this module does **not** modify any global random state
automatically; callers must invoke `set_seed()` explicitly.
"""

from __future__ import annotations

import random
import numpy as np

# Constant seed used throughout the project
SEED: int = 42

def _set_torch_seed(seed: int) -> None:
    """
    Set the seed for PyTorch if the library is available.

    Parameters
    ----------
    seed : int
        The seed value to set.
    """
    try:
        import torch
        torch.manual_seed(seed)
        # Ensure deterministic behavior for CUDA kernels if a GPU is present
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch is optional; silently ignore if not installed.
        pass

def set_seed(seed: int | None = None) -> None:
    """
    Set the random seed for reproducibility across supported libraries.

    If ``seed`` is ``None`` the module‑level constant ``SEED`` is used.

    Parameters
    ----------
    seed : int | None, optional
        The seed to set.  Defaults to ``None`` which resolves to ``SEED``.
    """
    actual_seed = SEED if seed is None else seed

    # Python's built‑in random module
    random.seed(actual_seed)

    # NumPy's random generator
    np.random.seed(actual_seed)

    # PyTorch (optional)
    _set_torch_seed(actual_seed)

__all__ = ["SEED", "set_seed"]
