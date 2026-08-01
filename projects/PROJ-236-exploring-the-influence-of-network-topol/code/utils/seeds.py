"""
Utility for managing random seeds across the project.

Provides a simple API to set a global NumPy random seed, ensuring reproducible
behaviour for any NumPy random number generation performed after the call.
The function also sets the Python built‑in ``random`` module seed for completeness.
"""

from __future__ import annotations

import random
from typing import Optional

import numpy as np

__all__ = ["set_global_seed", "get_global_seed"]

# Store the most recent seed for introspection; ``None`` means no seed has been set yet.
_current_seed: Optional[int] = None


def set_global_seed(seed: int) -> None:
    """
    Set the global random seed for NumPy and the built‑in ``random`` module.

    Parameters
    ----------
    seed: int
        The seed value to use. Must be a non‑negative integer.

    Raises
    ------
    TypeError
        If ``seed`` is not an ``int``.
    ValueError
        If ``seed`` is negative.

    The function records the seed internally so that callers can retrieve it
    via :func:`get_global_seed` if needed.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an int, got {type(seed)}")
    if seed < 0:
        raise ValueError("Seed must be non‑negative")
    global _current_seed
    _current_seed = seed
    np.random.seed(seed)
    random.seed(seed)


def get_global_seed() -> Optional[int]:
    """
    Return the most recent seed set by :func:`set_global_seed`, or ``None`` if
    no seed has been set yet.
    """
    return _current_seed
