"""
Correlation analysis module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS

def calculate_correlation(x: pd.Series, y: pd.Series, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate Pearson or Spearman correlation.
    
    Args:
        x: Series 1
        y: Series 2
        method: 'pearson' or 'spearman'
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if method == 'pearson':
        corr, p_val = stats.pearsonr(x, y)
    elif method == 'spearman':
        corr, p_val = stats.spearmanr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(corr), float(p_val)

def circular_block_permutation(x: pd.Series, y: pd.Series, iterations: int = PERMUTATION_ITERATIONS, alpha: float = 0.05) -> Tuple[float, bool]:
    """
    Perform circular block permutation test to assess significance.
    
    Args:
        x: Series 1
        y: Series 2
        iterations: Number of permutations
        alpha: Significance level
    
    Returns:
        Tuple of (p_value, is_significant)
    """
    n = len(x)
    obs_corr, _ = calculate_correlation(x, y, method='pearson')
    
    permuted_corrs = []
    for _ in range(iterations):
        # Circular shift y
        shift = np.random.randint(1, n)
        y_perm = np.roll(y.values, shift)
        perm_corr, _ = calculate_correlation(x, pd.Series(y_perm), method='pearson')
        permuted_corrs.append(perm_corr)
    
    permuted_corrs = np.array(permuted_corrs)
    # Two-tailed p-value
    extreme_count = np.sum(np.abs(permuted_corrs) >= np.abs(obs_corr))
    p_val = extreme_count / iterations
    
    is_significant = p_val < alpha
    return float(p_val), is_significant

def moving_block_bootstrap(x: pd.Series, y: pd.Series, iterations: int = BOOTSTRAP_ITERATIONS, block_size: int = 10) -> Tuple[float, float]:
    """
    Moving block bootstrap for confidence intervals.
    
    Args:
        x: Series 1
        y: Series 2
        iterations: Number of bootstrap iterations
        block_size: Size of blocks
    
    Returns:
        Tuple of (mean_corr, 95% CI) - simplified to return mean and bounds
    """
    n = len(x)
    boot_corrs = []
    
    for _ in range(iterations):
        indices = []
        while len(indices) < n:
            start = np.random.randint(0, n - block_size + 1)
            indices.extend(range(start, start + block_size))
        indices = indices[:n]
        
        x_boot = x.iloc[indices].values
        y_boot = y.iloc[indices].values
        corr, _ = calculate_correlation(pd.Series(x_boot), pd.Series(y_boot), method='pearson')
        boot_corrs.append(corr)
    
    boot_corrs = np.array(boot_corrs)
    mean_corr = np.mean(boot_corrs)
    ci_low, ci_high = np.percentile(boot_corrs, [2.5, 97.5])
    
    return float(mean_corr), (float(ci_low), float(ci_high))
