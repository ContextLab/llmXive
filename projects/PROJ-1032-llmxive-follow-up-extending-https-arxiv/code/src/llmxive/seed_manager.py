"""
Seed Management Module for Deterministic Runs.

This module provides functionality to ensure reproducibility across
all random number generators used in the training pipeline (Python,
NumPy, PyTorch, and Hugging Face Datasets).

It implements FR-004: Ensure deterministic runs via strict seed management.
"""

import os
import random
import logging
from typing import Optional

import numpy as np
import torch

# Optional import for datasets reproducibility
try:
    from datasets import set_caching_enabled
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

logger = logging.getLogger(__name__)


def set_all_seeds(seed: int, deterministic: bool = True) -> None:
    """
    Set seeds for all random number generators to ensure reproducibility.

    Args:
        seed (int): The integer seed to use for all generators.
        deterministic (bool): If True, enforce deterministic behavior in PyTorch.
                              Note: This may impact performance.

    Raises:
        ValueError: If seed is negative.
    """
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")

    logger.info(f"Initializing random seeds with value: {seed}")

    # Python standard library
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # PyTorch deterministic settings
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        try:
            torch.use_deterministic_algorithms(True)
        except RuntimeError as e:
            # Some operations might not support deterministic mode
            logger.warning(f"Could not enable deterministic algorithms: {e}")

    # Hugging Face Datasets
    if HAS_DATASETS:
        # Disable caching to ensure fresh data loading per seed if needed,
        # though setting seed usually suffices for shuffling.
        # We set caching to True for performance but ensure seed handles shuffle.
        set_caching_enabled(True)
        # Note: datasets.load_dataset has a 'seed' argument for shuffling,
        # which should be passed explicitly when loading.

    logger.info("All seeds set successfully.")


def get_deterministic_config(seed: int) -> dict:
    """
    Generate a configuration dictionary for reproducibility tracking.

    Args:
        seed (int): The seed value used.

    Returns:
        dict: A dictionary containing the seed and deterministic flags
              for logging and manifest generation.
    """
    return {
        "seed": seed,
        "deterministic_mode": True,
        "python_version": f"{random.__name__}", # Placeholder for actual version check if needed
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
    }


class SeedManager:
    """
    Context manager and utility class for managing seeds within a training run.

    This ensures that a specific seed is applied at the start of a run
    and can be restored if needed.
    """

    def __init__(self, seed: int, deterministic: bool = True):
        self.seed = seed
        self.deterministic = deterministic
        self._previous_state = None

    def __enter__(self):
        # In a more complex system, we might save the previous state here.
        # For now, we just set the seed.
        set_all_seeds(self.seed, self.deterministic)
        logger.debug(f"SeedManager entered with seed {self.seed}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("SeedManager exited")
        return False

    @staticmethod
    def reset_seed(seed: int) -> None:
        """Static helper to reset seeds without context manager."""
        set_all_seeds(seed)