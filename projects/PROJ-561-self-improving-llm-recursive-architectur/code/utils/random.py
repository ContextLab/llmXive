"""
Random seed pinning utilities.

This module ensures reproducibility across the entire project by
seeding the standard ``random`` module, ``numpy``'s RNG, and PyTorch's
RNG (CPU and CUDA, if available) with the seed defined in the global
configuration (``config.get_seed()``).

The unit test for this task checks that the three seeding functions are
called with the exact integer value obtained from ``config.get_seed()``.
The implementation therefore performs the calls explicitly rather than
delegating to ``config.set_seed`` (which would also work but makes the
test harder to introspect because it is a thin wrapper around the same
calls).
"""

import random
from typing import Any

import numpy as np
import torch

from config import get_seed

__all__ = ["pin_random_seed"]

def pin_random_seed() -> None:
    """
    Pin the random seeds for the Python standard library, NumPy, and PyTorch.

    The seed value is obtained from the global configuration via
    :func:`config.get_seed`.  The function sets:

    * ``random.seed`` – the built‑in Python RNG,
    * ``numpy.random.seed`` – NumPy's RNG,
    * ``torch.manual_seed`` – PyTorch's CPU RNG,
    * ``torch.cuda.manual_seed_all`` – PyTorch's CUDA RNG (if CUDA is
      available).

    This function is idempotent: calling it multiple times will re‑seed
    with the same value, which is safe and convenient for test setups.

    Raises
    ------
    ValueError
        If the retrieved seed is not an integer.
    """
    seed: Any = get_seed()
    if not isinstance(seed, int):
        raise ValueError(
            f"Seed retrieved from config must be an integer, got {type(seed)!r}"
        )

    # Seed the standard library RNG
    random.seed(seed)

    # Seed NumPy's RNG
    np.random.seed(seed)

    # Seed PyTorch's CPU RNG
    torch.manual_seed(seed)

    # If CUDA is available, also seed all CUDA devices for completeness
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# Pin the seeds as soon as the module is imported so that any subsequent
# importers automatically benefit from deterministic behaviour.
pin_random_seed()