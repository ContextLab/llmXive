"""
Reproducibility seed helper (T000).

Calling :func:`set_seeds` fixes the global seeds of the Python standard
library ``random`` module, NumPy, and (when installed) PyTorch, and pins
``PYTHONHASHSEED`` so that hash-based behaviour is also deterministic.

The canonical project seed is 42.  After ``set_seeds(42)`` the first call
to ``np.random.rand()`` returns 0.3745401188473625, which is the reference
value asserted by ``tests/test_setup.py``.
"""

import os
import random
from typing import Any, Dict

import numpy as np

DEFAULT_SEED: int = 42

def set_seeds(seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """
    Set global random seeds for reproducibility.

    Parameters
    ----------
    seed:
        The seed value to use for every RNG (default 42).

    Returns
    -------
    Dict[str, Any]
        A summary of the seed configuration, useful for logging.
    """
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    # PyTorch is optional at this stage of the pipeline; only seed it
    # when it is actually importable (it is a heavy dependency).
    torch_seeded = False
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():  # pragma: no cover - CPU-only CI
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch_seeded = True
    except ImportError:
        pass

    return {
        "seed": seed,
        "python_random": True,
        "numpy": True,
        "pythonhashseed": str(seed),
        "torch": torch_seeded,
    }

def get_seed_state_summary() -> Dict[str, Any]:
    """Return a small summary of the current seeding configuration."""
    return {
        "default_seed": DEFAULT_SEED,
        "pythonhashseed_env": os.environ.get("PYTHONHASHSEED"),
    }
