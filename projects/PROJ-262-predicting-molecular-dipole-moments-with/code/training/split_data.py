from __future__ import annotations

import numpy as np
from typing import Tuple, List

def get_train_test_splits(n_samples: int, seed: int = 42, test_ratio: float = 0.2) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate reproducible train/test splits for a given seed.
    
    Args:
        n_samples: Total number of samples
        seed: Random seed for reproducibility
        test_ratio: Proportion of data to use for testing
        
    Returns:
        Tuple of (train_indices, test_indices) as numpy arrays
    """
    np.random.seed(seed)
    indices = np.arange(n_samples)
    np.random.shuffle(indices)
    
    split_idx = int(len(indices) * (1 - test_ratio))
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    return train_indices, test_indices
