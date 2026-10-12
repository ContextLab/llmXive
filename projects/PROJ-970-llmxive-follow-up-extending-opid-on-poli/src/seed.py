"""
Seed management module.

This module provides thin wrappers around the central configuration's seed
handling functions. Importing this module automatically seeds the random
number generators to ensure deterministic behaviour across runs.

Public API:
  - set_seed(seed: Optional[int] = None) -> None
  - get_seed() -> Optional[int]
  - initialize_reproducibility() -> None
"""

import os
import random
from typing import Optional

import numpy as np

# Import the central configuration utilities.
# The config module lives at the project root (importable as `config`).
from config import set_seed as _config_set_seed
from config import get_seed as _config_get_seed

__all__ = ["set_seed", "get_seed", "initialize_reproducibility"]


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for NumPy, the standard ``random`` module, and the
    ``PYTHONHASHSEED`` environment variable.

    If ``seed`` is ``None``, the seed defined in ``config.SEED`` (or the
    currently stored seed in the configuration) will be used.

    Parameters
    ----------
    seed : Optional[int]
        Seed value to initialise reproducibility. ``None`` delegates to
        ``config.set_seed`` which uses the default project seed.
    """
    # Delegate to the central configuration implementation.
    _config_set_seed(seed)


def get_seed() -> Optional[int]:
    """
    Retrieve the current active seed.

    Returns
    -------
    Optional[int]
        The seed that was set by the most recent call to ``set_seed``.
    """
    return _config_get_seed()


def initialize_reproducibility() -> None:
    """
    Initialise reproducibility at import time.

    This function is invoked automatically when the module is imported,
    ensuring that any subsequent code runs with a deterministic RNG state.
    """
    set_seed()


# Automatically initialise reproducibility when the module is imported.
initialize_reproducibility()