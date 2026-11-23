import numpy as np
from typing import List, Tuple, Optional
from config import get_bootstrap_seed, get_shuffle_seed

def standard_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list:
    """
    Perform standard non-parametric bootstrap.
    Resamples the data with replacement and calculates the mean for each resample.
    """
    np.random.seed(seed)
    n = len(data)
    bootstrap_means = []
    
    for _ in range(n_resamples):
        # Resample with replacement
        resample = np.random.choice(data, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    return bootstrap_means

def shuffled_bootstrap(data: np.ndarray, n_resamples: int, seed: int) -> list:
    """
    Perform bootstrap on shuffled data to break temporal dependence.
    """
    np.random.seed(seed)
    # Shuffle the data first
    shuffled_data = np.random.permutation(data)
    
    n = len(shuffled_data)
    bootstrap_means = []
    
    for _ in range(n_resamples):
        # Resample with replacement from shuffled data
        resample = np.random.choice(shuffled_data, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    return bootstrap_means

def calculate_ci_from_resamples(resamples: List[float], alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate confidence interval from bootstrap resamples using percentile method.
    """
    if not resamples:
        raise ValueError("Resamples list cannot be empty.")
    
    sorted_resamples = sorted(resamples)
    n = len(sorted_resamples)
    
    lower_idx = int((alpha / 2) * n)
    upper_idx = int((1 - alpha / 2) * n)
    
    # Handle edge cases
    lower_idx = max(0, lower_idx)
    upper_idx = min(n - 1, upper_idx)
    
    return sorted_resamples[lower_idx], sorted_resamples[upper_idx]
