"""
Utility module to set deterministic seeds across the pipeline.
"""

import random
import numpy as np
import torch

def set_global_seed(seed: int = 42) -> None:
    """
    Set the random seed for Python's `random`, NumPy, and PyTorch.

    Parameters
    ----------
    seed : int, optional
        The seed value to use. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    # Ensure deterministic behavior on CPU
    torch.use_deterministic_algorithms(True)

# Set the default seed at import time
set_global_seed(42)
