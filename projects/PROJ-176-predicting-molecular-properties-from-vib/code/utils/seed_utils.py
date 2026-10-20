"""
Simple seed‑setting utility to make runs reproducible.
"""

import random
import numpy as np

def set_seed(seed: int = 0) -> None:
    """
    Set seeds for Python's ``random``, NumPy, and (optionally) PyTorch (CPU only).

    The function attempts to import ``torch`` lazily; if PyTorch is not installed
    the function still sets the Python and NumPy seeds and returns without error.
    This allows parts of the pipeline that do not require PyTorch (e.g. the
    data‑download step) to run on systems where the ``torch`` package is absent.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Lazy import of torch – only needed for training/evaluation stages.
    try:
        import torch

        torch.manual_seed(seed)

        # Ensure deterministic behavior for PyTorch CPU ops
        torch.use_deterministic_algorithms(True)
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch not available; that's fine for download/preprocess steps.
        pass