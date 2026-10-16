"""
Simple seed‑setting utility to make runs reproducible.
"""

import random
import numpy as np
import torch

def set_seed(seed: int = 0) -> None:
    """
    Set seeds for Python's ``random``, NumPy, and PyTorch (CPU only).

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    # Ensure deterministic behavior for PyTorch CPU ops
    torch.use_deterministic_algorithms(True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
