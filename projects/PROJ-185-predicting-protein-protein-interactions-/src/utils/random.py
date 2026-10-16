"""
src/utils/random.py
--------------------
Utility module for managing a global random seed across the project.

This module provides a simple API to set and retrieve the global seed.
It synchronises the seed across the standard ``random`` module,
``numpy.random`` and (optionally) ``torch`` if the library is available.
All stochastic functions in the pipeline should import ``set_seed`` from
this module and call it once during initialisation (typically right after
parsing command‑line arguments).
"""

import random as _py_random
from typing import Optional

import numpy as _np

_GLOBAL_SEED: Optional[int] = None

def set_seed(seed: int) -> None:
    """
    Initialise the global random seed.

    Parameters
    ----------
    seed : int
        Seed value to initialise the RNGs.

    This function sets the seed for:
    * Python's built‑in ``random`` module
    * NumPy's random generator
    * PyTorch (if installed) – the call is ignored otherwise

    The seed is stored in a module‑level variable so that it can be
    retrieved later via :func:`get_seed`.
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = int(seed)

    # Standard library RNG
    _py_random.seed(seed)

    # NumPy RNG
    _np.random.seed(seed)

    # Optional Torch RNG – ignored if torch is not installed
    try:
        import torch
        torch.manual_seed(seed)
    except Exception:
        # Torch is not a mandatory dependency; silently ignore.
        pass

def get_seed() -> Optional[int]:
    """
    Return the currently configured global seed.

    Returns
    -------
    Optional[int]
        The seed set by :func:`set_seed`, or ``None`` if no seed has been
        configured yet.
    """
    return _GLOBAL_SEED
