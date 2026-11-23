"""
Utility module for managing a global random seed across the project.

This module provides a simple API:
- `set_seed(seed: int)`: Set the global seed for Python's `random`,
  NumPy's RNG, and (if available) PyTorch.
- `get_seed() -> int | None`: Retrieve the currently set seed.

All stochastic components of the pipeline should import this module
and call `set_seed` once at the start of the run (e.g. from the CLI
parser). Subsequent calls to random functions will then be fully
reproducible.
"""
import random
from typing import Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

_CURRENT_SEED: Optional[int] = None


def set_seed(seed: int) -> None:
    """
    Set the global random seed for the standard library, NumPy and
    PyTorch (if installed).

    Parameters
    ----------
    seed : int
        The seed value to use for all RNGs.
    """
    global _CURRENT_SEED
    _CURRENT_SEED = seed

    random.seed(seed)

    if np is not None:
        np.random.seed(seed)

    if torch is not None:
        torch.manual_seed(seed)
        # Ensure deterministic behavior on CPU/GPU when torch is used.
        torch.use_deterministic_algorithms(True)


def get_seed() -> Optional[int]:
    """
    Return the currently configured seed, or ``None`` if no seed has
    been set yet.

    Returns
    -------
    int | None
        The global seed value.
    """
    return _CURRENT_SEED
