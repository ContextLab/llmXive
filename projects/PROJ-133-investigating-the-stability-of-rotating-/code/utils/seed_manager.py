"""Random‑seed management utilities.

The module provides deterministic seed handling for reproducible
simulations.  Public functions are documented with NumPy‑style docstrings.
"""

import random
from typing import Optional

_global_seed: Optional[int] = None

def set_seed(seed: int) -> None:
    """Set the global random seed for NumPy and Python's ``random`` module.

    Parameters
    ----------
    seed : int
        Seed value to initialise the RNGs.
    """
    global _global_seed
    _global_seed = seed
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

def get_global_seed() -> Optional[int]:
    """Return the currently set global seed.

    Returns
    -------
    int or None
        The seed value if ``set_seed`` has been called; otherwise ``None``.
    """
    return _global_seed
