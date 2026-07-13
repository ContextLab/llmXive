from __future__ import annotations

import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility across Python, NumPy, and PyTorch.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
