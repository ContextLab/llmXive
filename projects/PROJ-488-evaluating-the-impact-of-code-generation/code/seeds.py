"""
Seed management module for reproducible experiments.

This module provides utilities for setting random seeds across multiple
libraries to ensure reproducible results in the code generation impact
evaluation pipeline.

Seed Value: 42 (documented constant for consistency across all experiments)
"""

import random
from typing import Optional


# Documented seed value for reproducibility
SEED_VALUE = 42


def set_seed(seed: int = SEED_VALUE) -> None:
    """
    Set random seeds for reproducibility across numpy, random, and torch.

    Args:
        seed: Integer seed value. Defaults to 42 (SEED_VALUE).
    """
    # Set seed for Python's built-in random module
    random.seed(seed)

    # Set seed for numpy
    import numpy as np
    np.random.seed(seed)

    # Set seed for torch if available (optional)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # Torch not installed, skip torch seeding
        pass


def get_seed_value() -> int:
    """
    Return the documented seed value used across the project.

    Returns:
        The seed value (42).
    """
    return SEED_VALUE
