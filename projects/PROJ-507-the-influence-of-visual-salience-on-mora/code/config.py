"""
Configuration module for reproducibility.
Sets random seeds for numpy, random, and torch upon import.
"""
import os
import random
from typing import Optional

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


DEFAULT_SEED = 42


def seed_everything(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across numpy, random, and torch.

    Args:
        seed: The integer seed value to use. Defaults to 42.
    """
    # Set environment variable for torch determinism
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Set seed for random
    random.seed(seed)

    # Set seed for numpy
    np.random.seed(seed)

    # Set seed for torch if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # if multi-GPU
            # Ensure deterministic behavior (may impact performance)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

# Execute immediately upon import to ensure seeds are set
# before any other stochastic operations occur in the pipeline.
seed_everything(DEFAULT_SEED)