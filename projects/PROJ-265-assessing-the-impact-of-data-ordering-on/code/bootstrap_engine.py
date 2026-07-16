"""
Bootstrap engine module for resampling and confidence interval calculation.

Provides standard and shuffled bootstrap methods for time series analysis.
"""
import numpy as np
from typing import List, Tuple, Optional
from config import get_bootstrap_seed, get_shuffle_seed


def standard_bootstrap(data: np.ndarray, n_resamples: int, seed: Optional[int] = None) -> List[np.ndarray]:
    """
    Perform standard non-parametric bootstrap resampling.
    
    Args:
        data: Input data array to resample from.
        n_resamples: Number of bootstrap resamples to generate.
        seed: Random seed for reproducibility. If None, uses config default.
    
    Returns:
        List of numpy arrays, each representing a bootstrap resample.
    """
    if seed is None:
        seed = get_bootstrap_seed()
    
    rng = np.random.default_rng(seed)
    n = len(data)
    resamples = []
    
    for _ in range(n_resamples):
        indices = rng.choice(n, size=n, replace=True)
        resamples.append(data[indices])
    
    return resamples


def shuffled_bootstrap(data: np.ndarray, n_resamples: int, seed: Optional[int] = None) -> List[np.ndarray]:
    """
    Perform bootstrap on shuffled data to break temporal dependence.
    
    Args:
        data: Input time series data.
        n_resamples: Number of bootstrap resamples to generate.
        seed: Random seed for reproducibility. If None, uses config default.
    
    Returns:
        List of numpy arrays representing bootstrap resamples of shuffled data.
    """
    if seed is None:
        seed = get_shuffle_seed()
    
    rng = np.random.default_rng(seed)
    shuffled_data = rng.permutation(data)
    
    return standard_bootstrap(shuffled_data, n_resamples, seed)


def calculate_ci_from_resamples(resamples: List[np.ndarray], alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate confidence interval from bootstrap resamples using percentile method.
    
    Args:
        resamples: List of bootstrap resample arrays.
        alpha: Significance level (default 0.05 for 95% CI).
    
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval.
    """
    means = np.array([np.mean(r) for r in resamples])
    lower = np.percentile(means, 100 * alpha / 2)
    upper = np.percentile(means, 100 * (1 - alpha / 2))
    return lower, upper
