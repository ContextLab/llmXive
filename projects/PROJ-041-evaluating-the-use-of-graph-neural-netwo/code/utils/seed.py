"""
seed.py
--------

Deterministic seed handling utilities.
Provides a single public function ``set_seed`` that seeds the Python
``random`` module, NumPy, and (if available) PyTorch for reproducible
experiments.
"""

import os
import random

import numpy as np

try:
    import torch
except Exception:  # torch may not be installed in minimal environments
    torch = None  # type: ignore


def set_seed(seed: int) -> None:
    """
    Set the random seed for Python's ``random``, NumPy, and PyTorch
    (if installed) to ensure deterministic behaviour.

    Parameters
    ----------
    seed: int
        The seed value to use.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)

    if torch is not None:
        torch.manual_seed(seed)