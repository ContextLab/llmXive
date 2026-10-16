"""
Utility module to pin random seeds for reproducibility across the project.
Imported by all scripts that perform stochastic operations.
"""
import random
import numpy as np

# Optional torch import – if torch is not installed, the import is ignored.
try:
    import torch
except ImportError:
    torch = None  # type: ignore

SEED = 42

def pin_seeds(seed: int = SEED) -> None:
    """
    Pin seeds for Python's random, NumPy, and (if available) PyTorch.
    This function should be called as early as possible in any script.
    """
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

# Pin seeds at import time so that any script that imports this module
# gets deterministic behavior immediately.
pin_seeds()
