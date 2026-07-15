"""
Correlation Analysis Module.

Calculates Pearson/Spearman correlations and performs permutation tests.

File path: code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS

def calculate_correlation(
    x: pd.Series, 
    y: pd.Series, 
    permutation_iterations: int = PERMUTATION_ITERATIONS
) -> Tuple[float, float, float, bool]:
    """
    Calculates Pearson and Spearman correlations and performs a permutation test.
    
    Args:
        x: First time series.
        y: Second time series.
        permutation_iterations: Number of iterations for the permutation test.
        
    Returns:
        Tuple of (pearson, spearman, p_val_permutation, significant_flag)
    """
    # Calculate correlations
    pearson, p_pearson = stats.pearsonr(x, y)
    spearman, p_spearman = stats.spearmanr(x, y)
    
    # Permutation test
    p_val_perm = circular_block_permutation(x, y, iterations=permutation_iterations)
    
    # Significance flag (p < 0.05)
    significant = p_val_perm < 0.05
    
    return pearson, spearman, p_val_perm, significant

def circular_block_permutation(
    x: pd.Series, 
    y: pd.Series, 
    iterations: int = PERMUTATION_ITERATIONS,
    block_size: Optional[int] = None
) -> float:
    """
    Performs a circular block permutation test to assess significance.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of permutations.
        block_size: Size of blocks to preserve temporal dependence.
        
    Returns:
        Empirical p-value.
    """
    n = len(x)
    if n != len(y):
        raise ValueError("Series must be of equal length")
    
    # Calculate observed correlation
    obs_corr, _ = stats.pearsonr(x, y)
    obs_corr = abs(obs_corr)
    
    # Determine block size
    if block_size is None:
        # Default block size: 10% of series or 5, whichever is larger
        block_size = max(5, int(n * 0.1))
    
    permuted_corrs = []
    
    for _ in range(iterations):
        # Circular shift y by a random amount
        shift = np.random.randint(1, n)
        y_perm = np.roll(y.values, shift)
        
        # Calculate correlation
        corr, _ = stats.pearsonr(x.values, y_perm)
        permuted_corrs.append(abs(corr))
    
    # Calculate p-value
    p_val = np.mean([c >= obs_corr for c in permuted_corrs])
    
    return p_val

def moving_block_bootstrap(
    x: pd.Series, 
    y: pd.Series, 
    iterations: int = BOOTSTRAP_ITERATIONS,
    block_size: Optional[int] = None
) -> Tuple[float, float]:
    """
    Performs moving block bootstrap to estimate confidence intervals.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of bootstrap iterations.
        block_size: Size of blocks.
        
    Returns:
        Tuple of (mean_corr, ci_95)
    """
    n = len(x)
    if block_size is None:
        block_size = max(5, int(n * 0.1))
    
    boot_corrs = []
    
    for _ in range(iterations):
        # Resample blocks
        indices = []
        while len(indices) < n:
            start = np.random.randint(0, n - block_size + 1)
            indices.extend(range(start, start + block_size))
        indices = indices[:n]
        
        x_boot = x.iloc[indices].values
        y_boot = y.iloc[indices].values
        
        corr, _ = stats.pearsonr(x_boot, y_boot)
        boot_corrs.append(corr)
    
    mean_corr = np.mean(boot_corrs)
    ci_lower = np.percentile(boot_corrs, 2.5)
    ci_upper = np.percentile(boot_corrs, 97.5)
    
    return mean_corr, (ci_lower, ci_upper)
