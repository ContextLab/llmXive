"""
Seed management module.

This module provides a deterministic way to pin the random number generators
used throughout the project (the standard library ``random`` module and
NumPy's RNG).  The seed value is stored internally so that downstream code
can retrieve it via :func:`get_seed`.

The implementation is deliberately lightweight and has no side‑effects
beyond setting the RNG states.  It is safe to call ``pin_seeds`` multiple
times – the most recent call overwrites the stored seed.
"""

from __future__ import annotations

import random
from typing import Optional

import numpy as np

from llmxive_toolkit import get_logger

# Initialise a logger for optional debugging output.
log = get_logger(__name__)

# Internal storage for the currently pinned seed.  ``None`` means that
# ``pin_seeds`` has not been called yet.
_current_seed: Optional[int] = None


def pin_seeds(seed: int) -> None:
    """
    Pin the global random seeds.

    This function sets the seed for both the standard library ``random``
    module and NumPy's random generator to ``seed``.  The value is stored
    internally and can be retrieved later via :func:`get_seed`.

    Parameters
    ----------
    seed : int
        The integer seed to use for deterministic execution.
    """
    global _current_seed
    _current_seed = seed

    # Pin the Python ``random`` module.
    random.seed(seed)

    # Pin NumPy's RNG.  NumPy respects the global seed via ``np.random.seed``.
    np.random.seed(seed)

    log.info("Global random seeds pinned to %s", seed)


def get_seed() -> int:
    """
    Return the seed that was most recently pinned.

    Raises
    ------
    RuntimeError
        If :func:`pin_seeds` has not been called yet.
    """
    if _current_seed is None:
        raise RuntimeError(
            "Seed has not been set. Call `pin_seeds(seed)` before requesting it."
        )
    return _current_seed