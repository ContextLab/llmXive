"""
Reproducibility utilities for the project.

This module pins global random seeds for the standard libraries used
throughout the code base:
- Python's built-in ``random`` module
- NumPy's random generator
- PyTorch (if installed)

The default seed is defined as ``SEED = 42`` to satisfy the verification
step required by task T001.

Importing this module automatically applies the seed, so any script that
imports ``code.utils.reproducibility`` will run deterministically
(subject to the usual constraints of deterministic algorithms).

Example verification command (must exit with status 0):
    python -c "import code.utils.reproducibility as r; assert r.SEED == 42"
"""

import os
import random

import numpy as np

# Public constant used by the verification test
SEED: int = 42

__all__ = ["SEED", "seed_all"]


def seed_all(seed: int = SEED) -> None:
    """
    Apply the given seed to all supported random number generators.

    Parameters
    ----------
    seed : int, optional
        The seed value to set. Defaults to the module‑level ``SEED`` (42).

    This function:
    - Sets ``PYTHONHASHSEED`` for reproducible hashing of built‑in types.
    - Seeds the ``random`` module.
    - Seeds NumPy's RNG.
    - If PyTorch is available, seeds its CPU and CUDA RNGs.
    """
    # Ensure hash‑based operations are deterministic
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Seed the standard library RNG
    random.seed(seed)

    # Seed NumPy RNG
    np.random.seed(seed)

    # Attempt to seed PyTorch if it is installed; otherwise ignore silently
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # PyTorch is optional; the pipeline can run without it.
        pass


# Apply the seed immediately upon import so that any module importing this
# file gets a deterministic environment without needing to call ``seed_all``.
seed_all()
