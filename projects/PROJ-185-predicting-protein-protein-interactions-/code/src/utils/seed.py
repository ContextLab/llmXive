"""
Utility for setting a global random seed across the Python process.

This module provides a single function `set_global_seed` that seeds the
built‑in ``random`` module, NumPy's random generator, and the ``PYTHONHASHSEED``
environment variable.  Down‑stream stochastic pipeline components (e.g.
correlation computation, baseline graph generation, negative sampling,
sensitivity analysis) rely on these libraries for randomness, so invoking this
function ensures reproducible behaviour throughout the pipeline.
"""

import os
import random

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

__all__ = ["set_global_seed"]


def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for the current Python process.

    Parameters
    ----------
    seed : int
        The seed value to use for all supported random number generators.

    This function:
    - Seeds the built‑in ``random`` module.
    - Seeds NumPy's RNG if NumPy is available.
    - Sets the ``PYTHONHASHSEED`` environment variable to make hash‑based
      operations deterministic.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)!r}")

    # Seed the standard library RNG
    random.seed(seed)

    # Seed NumPy RNG if available
    if np is not None:
        np.random.seed(seed)

    # Ensure hash randomization is deterministic
    os.environ["PYTHONHASHSEED"] = str(seed)
