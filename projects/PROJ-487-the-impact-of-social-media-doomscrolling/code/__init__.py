"""
llmXive - The Impact of Social Media Doomscrolling on Anticipatory Anxiety
Project initialization and deterministic reproducibility setup.
"""

import os
import random
import sys
from typing import Optional

# Ensure numpy is available for seeding (optional but recommended)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Ensure torch is available for seeding if used later (optional)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Default seed if not provided via environment
DEFAULT_SEED = 42
SEED_ENV_VAR = "PYTHONHASHSEED"
RANDOM_SEED_ENV_VAR = "RANDOM_SEED"


def set_deterministic_seed(seed: Optional[int] = None) -> int:
    """
    Sets deterministic random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Args:
        seed: Optional integer seed. If None, reads from RANDOM_SEED env var or defaults to 42.
    
    Returns:
        The seed value that was set.
    
    Raises:
        ValueError: If the seed is not a non-negative integer.
    """
    if seed is None:
        seed_str = os.environ.get(RANDOM_SEED_ENV_VAR)
        if seed_str is not None:
            try:
                seed = int(seed_str)
            except ValueError:
                raise ValueError(f"Invalid seed value in {RANDOM_SEED_ENV_VAR}: {seed_str}. Must be an integer.")
        else:
            seed = DEFAULT_SEED

    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy seed if available
    if HAS_NUMPY:
        np.random.seed(seed)

    # Set PyTorch seeds if available
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Set PYTHONHASHSEED for hash randomization control
    os.environ[SEED_ENV_VAR] = str(seed)

    return seed


# Execute seed pinning on module import to ensure reproducibility from the start
_seed_value = set_deterministic_seed()


__all__ = [
    "set_deterministic_seed",
    "DEFAULT_SEED",
    "SEED_ENV_VAR",
    "RANDOM_SEED_ENV_VAR",
    "HAS_NUMPY",
    "HAS_TORCH",
]

__version__ = "0.1.0"