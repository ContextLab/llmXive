"""
Seed management utility for reproducible experiments.

Provides functions to generate multiple independent random seeds
for training runs, ensuring statistical robustness.
"""

import random
from typing import List

import numpy as np
import torch


def get_seeds(n: int, base_seed: int = 42) -> List[int]:
    """
    Generate a list of n unique integer seeds derived from a base seed.

    This ensures that multiple training runs are independent yet reproducible
    if the base seed is fixed.

    Args:
        n (int): Number of seeds to generate.
        base_seed (int): The base seed to derive others from. Default is 42.

    Returns:
        List[int]: A list of n unique integer seeds.

    Raises:
        ValueError: If n is not a positive integer.
    """
    if n <= 0:
        raise ValueError("Number of seeds 'n' must be a positive integer.")

    seeds = []
    rng = random.Random(base_seed)

    # Generate n unique seeds
    while len(seeds) < n:
        seed = rng.randint(0, 2**32 - 1)
        if seed not in seeds:
            seeds.append(seed)

    return seeds


def set_global_seed(seed: int) -> None:
    """
    Set the random seed for Python's random, NumPy, and PyTorch.

    Args:
        seed (int): The seed value to set.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Ensure deterministic behavior in PyTorch operations
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False