"""
Environment configuration management for random seeds.

This module provides a centralized way to set and retrieve random seeds
for reproducibility across NumPy, Python's random module, and PyTorch.
It ensures that all stochastic processes in the pipeline are seeded
consistently when a master seed is provided.
"""
import os
import random
import logging
from typing import Optional

import numpy as np

# Attempt to import torch; handle gracefully if not present (though required by project)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)

# Default seed value if none is provided via environment or argument
DEFAULT_SEED = 42

# Environment variable name for the master seed
SEED_ENV_VAR = "LLMXIVE_RANDOM_SEED"


def get_seed() -> int:
    """
    Retrieve the master random seed.

    Priority order:
    1. Function argument (if called programmatically)
    2. Environment variable 'LLMXIVE_RANDOM_SEED'
    3. Default value (42)

    Returns:
        int: The seed value to use.
    """
    # Check environment variable first
    env_seed = os.environ.get(SEED_ENV_VAR)
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            logger.warning(
                f"Invalid seed value in environment variable {SEED_ENV_VAR}: '{env_seed}'. "
                f"Using default seed {DEFAULT_SEED}."
            )
    return DEFAULT_SEED


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all libraries.

    This function configures seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (CPU and CUDA if available)
    - Python's hash randomization (via PYTHONHASHSEED environment variable)

    Args:
        seed (int, optional): The seed to use. If None, retrieves from
                              environment or uses default.

    Returns:
        int: The seed that was set.
    """
    if seed is None:
        seed = get_seed()

    # Ensure integer type
    seed = int(seed)

    # Set Python random seed
    random.seed(seed)

    # Set NumPy seed
    np.random.seed(seed)

    # Set PyTorch seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN (may impact performance)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Set PYTHONHASHSEED for consistent dictionary ordering
    os.environ["PYTHONHASHSEED"] = str(seed)

    logger.info(f"Random seeds initialized with master seed: {seed}")

    return seed


def ensure_seeded() -> int:
    """
    Ensure seeds are set before any other operations run.

    This is useful for entry points (like main functions) to guarantee
    reproducibility without needing explicit calls elsewhere.

    Returns:
        int: The seed that was set.
    """
    return set_seed()
