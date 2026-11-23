"""
Utility to set deterministic random seeds across the Python ecosystem
for reproducible experiments.

This module provides a single function ``set_random_seed`` which seeds
the following libraries:

- Python's built‑in ``random`` module
- NumPy's random generator
- PyTorch's CPU and CUDA RNGs

The function is deliberately lightweight and has no side effects
beyond seeding; it does not alter global PyTorch deterministic
settings (e.g., cudnn flags) because those are often controlled
elsewhere in the training pipeline.
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch


def set_random_seed(seed: int) -> None:
    """
    Set the random seed for ``random``, ``numpy`` and ``torch``.

    Parameters
    ----------
    seed: int
        The seed value to use for all RNGs.

    Notes
    -----
    - ``random.seed`` seeds Python's built‑in RNG.
    - ``numpy.random.seed`` seeds NumPy's legacy RNG.
    - ``torch.manual_seed`` seeds the CPU RNG for PyTorch.
    - ``torch.cuda.manual_seed_all`` seeds all CUDA devices, if any.
    """
    # Seed Python's built‑in RNG
    random.seed(seed)

    # Seed NumPy's RNG
    np.random.seed(seed)

    # Seed PyTorch CPU RNG
    torch.manual_seed(seed)

    # If CUDA is available, also seed its RNGs to keep full
    # reproducibility across devices.
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Ensure that operations are deterministic where possible.
    # These flags are optional but help guarantee reproducibility.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
