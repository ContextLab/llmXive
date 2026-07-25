"""
Specific fixtures for Block Bootstrap injection validation.
Supports T009 requirements for mock data fixtures.
"""
import numpy as np
from typing import List, Tuple

def create_hierarchical_data(
    n_groups: int, 
    group_size: int, 
    seed: int = 42
) -> np.ndarray:
    """
    Creates data with a simple hierarchical structure (groups)
    to test block bootstrap logic.
    
    Args:
        n_groups: Number of groups.
        group_size: Size of each group.
        seed: Random seed.
        
    Returns:
        1D array of data points with group structure.
    """
    rng = np.random.default_rng(seed)
    data = []
    for g in range(n_groups):
        # Each group has a random mean shift
        group_mean = rng.normal(0, 1)
        group_data = rng.normal(group_mean, 1, group_size)
        data.extend(group_data)
    return np.array(data)
