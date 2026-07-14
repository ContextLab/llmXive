from __future__ import annotations

"""
Utility module for reproducibility across the project.
Sets random seeds for Python's ``random``, NumPy, and PyTorch.
Also patches the local ``numpy`` stub (if present) to expose a ``__version__``
attribute required by downstream libraries such as pandas and scipy.
"""

import random
import numpy as np
import torch

# ---------------------------------------------------------------------------
# Patch local ``numpy`` stub (if it exists) to provide ``__version__``.
# Some environments ship a minimal ``numpy`` package that lacks the
# ``__version__`` attribute, causing import errors in pandas / scipy.
# We defensively add a version string when missing.
# ---------------------------------------------------------------------------
if not hasattr(np, "__version__"):
    # The actual version is not critical for the project's logic – we only need
    # the attribute to exist so that ``pandas`` and ``scipy`` can import safely.
    np.__version__ = "1.26.0"

def set_seed(seed: int = 42) -> None:
    """
    Set deterministic seeds for reproducibility.

    Parameters
    ----------
    seed : int
        Seed value to use for ``random``, ``numpy`` and ``torch``.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    # Ensure deterministic behavior for CUDA (if ever used)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False