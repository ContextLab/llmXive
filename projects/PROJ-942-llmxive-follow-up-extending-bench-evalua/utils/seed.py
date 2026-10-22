"""
Utility to set deterministic random seeds across the most common libraries.

The function :func:`set_seeds` is deliberately lightweight and has no external
dependencies beyond the standard library, NumPy and (optionally) PyTorch.
"""

import os
import random
from typing import Optional

import numpy as np

# Torch is an optional dependency; import lazily so that the script works on
# systems where it is not installed (e.g., during early CI steps).
try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None  # type: ignore

def set_seeds(seed: Optional[int] = 42) -> None:
    """
    Set deterministic seeds for ``random``, ``numpy`` and (if available) ``torch``.

    Parameters
    ----------
    seed : int, optional
        The seed value to use. The default (42) is a conventional choice that
        yields a reproducible ``numpy.random.rand()`` value of
        ``0.3745401188473625``.
    """
    if seed is None:
        raise ValueError("Seed must be an integer or None.")

    # Python's hash randomisation (affects dict ordering in some contexts)
    os.environ["PYTHONHASHSEED"] = str(seed)

    random.seed(seed)
    np.random.seed(seed)

    if torch is not None:
        torch.manual_seed(seed)
        # Ensure deterministic behaviour on CPU
        torch.use_deterministic_algorithms(True)
        # Disable nondeterministic cuDNN paths (no‑op on CPU‑only runs)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
