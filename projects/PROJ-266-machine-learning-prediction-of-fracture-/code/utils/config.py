"""
Configuration management for random seeds.

This module provides centralized seed management to ensure reproducibility
across the machine learning pipeline.

- Fixed seed (42) is used for data splits to ensure consistent train/val/test
  distribution across experiments.
- Variable seeds are supported for training runs to allow for multiple
  independent training instances.
"""

import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any


# Fixed seed for data splits (stratified split, etc.)
SPLIT_SEED = 42

# Default seed for training if none is provided
DEFAULT_TRAIN_SEED = 42


def set_seed(seed: int) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.

    Args:
        seed (int): The random seed to set.
    """
    # Python's random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior on CUDA
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Environment variable for deterministic behavior
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_split_seed() -> int:
    """
    Get the fixed seed used for data splits.

    Returns:
        int: The split seed (always 42).
    """
    return SPLIT_SEED


def get_training_seed(seed: Optional[int] = None) -> int:
    """
    Get the seed for a training run.

    If a seed is provided, it is used. Otherwise, the default seed (42) is used.
    This allows for multiple independent training runs with different seeds
    while maintaining reproducibility within each run.

    Args:
        seed (Optional[int]): The seed for this training run. If None, uses DEFAULT_TRAIN_SEED.

    Returns:
        int: The seed to use for training.
    """
    if seed is not None:
        return seed
    return DEFAULT_TRAIN_SEED


def init_random_state(split: bool = False, train_seed: Optional[int] = None) -> Dict[str, int]:
    """
    Initialize random state for a specific operation.

    This is a convenience function that sets seeds appropriately based on the
    operation type.

    Args:
        split (bool): If True, use the fixed split seed. If False, use a training seed.
        train_seed (Optional[int]): The seed for training if split is False.

    Returns:
        Dict[str, int]: A dictionary containing the seed used for verification.
    """
    if split:
        seed = SPLIT_SEED
    else:
        seed = get_training_seed(train_seed)

    set_seed(seed)
    return {"seed": seed}


def get_config_dict() -> Dict[str, Any]:
    """
    Get a dictionary of all configuration values.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    return {
        "split_seed": SPLIT_SEED,
        "default_train_seed": DEFAULT_TRAIN_SEED,
    }