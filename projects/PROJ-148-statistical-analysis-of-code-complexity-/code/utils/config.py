"""
Configuration utilities for the project.

This module centralises configuration handling that is required across the
code‑base, most notably the deterministic random‑seed handling used by the
data‑processing and modelling pipelines.

The public API consists of:
- ``DEFAULT_SEED`` – the fallback seed value (42).
- ``get_seed()`` – retrieve the seed from the ``RANDOM_SEED`` environment
  variable or fall back to ``DEFAULT_SEED``.
- ``set_random_seed(seed: int | None = None)`` – set the seed for the
  standard library :pymod:`random`, :pymod:`numpy.random`, and, if available,
  :pymod:`torch` to ensure reproducibility.
- ``Config`` – a simple ``dataclass`` that can be extended with additional
  configuration fields in the future.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

__all__ = [
    "DEFAULT_SEED",
    "get_seed",
    "set_random_seed",
    "Config",
]

# --------------------------------------------------------------------------- #
# Default configuration values
# --------------------------------------------------------------------------- #
DEFAULT_SEED: int = 42
"""Fallback random seed used when no explicit seed is supplied."""


# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def get_seed() -> int:
    """
    Retrieve the random seed from the ``RANDOM_SEED`` environment variable.

    Returns
    -------
    int
        The seed value. If the environment variable is not set or cannot be
        parsed as an integer, ``DEFAULT_SEED`` is returned.
    """
    env_val = os.getenv("RANDOM_SEED")
    if env_val is None:
        return DEFAULT_SEED
    try:
        return int(env_val)
    except ValueError:
        # If the variable is not an integer, fall back to the default.
        return DEFAULT_SEED


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set the seed for all supported random number generators.

    Parameters
    ----------
    seed : int | None, optional
        The seed to use. If ``None`` the seed is obtained via :func:`get_seed`.

    Returns
    -------
    int
        The seed that was actually used.
    """
    if seed is None:
        seed = get_seed()

    # Standard library ``random``
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch – optional, only set if the library is available.
    try:
        import torch

        torch.manual_seed(seed)
        # Ensure deterministic behavior for CUDA (if used)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch is not a hard dependency; silently ignore.
        pass

    return seed


# --------------------------------------------------------------------------- #
# Configuration dataclass
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    """
    Simple configuration container.

    The class can be expanded with additional configuration fields as the
    project grows. For now it only stores the random seed.
    """

    seed: int = field(default_factory=get_seed)

    def __post_init__(self) -> None:
        """
        Apply the seed to the relevant libraries as soon as the config is
        instantiated.
        """
        set_random_seed(self.seed)
