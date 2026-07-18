"""
Utility Functions for the Embodied Curriculum Learning Pipeline.

This module provides helper functions for setting random seeds, logging,
and other common operations across the pipeline to ensure reproducibility.
"""
import random
import os
from typing import Optional
import numpy as np
import logging


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across the entire pipeline.

    This function ensures deterministic behavior by seeding:
    1. Python's built-in `random` module.
    2. NumPy's random number generator.
    3. The `PYTHONHASHSEED` environment variable (affects dict/set hashing).

    Args:
        seed: Integer seed value. Must be non-negative.

    Raises:
        ValueError: If seed is negative.
    """
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")

    logger = logging.getLogger(__name__)
    logger.info(f"Setting random seed to {seed}")

    # Seed Python's random module
    random.seed(seed)

    # Seed NumPy
    np.random.seed(seed)

    # Set environment variable for hash reproducibility
    # This must be set before any dicts/sets are created in the process
    os.environ['PYTHONHASHSEED'] = str(seed)

    logger.debug("Random seed configuration complete.")