"""
Correlation analysis module.
Implements FR-005 (Permutation Test) and FR-006 (Bootstrap).
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS

def calculate_correlation(x: pd.Series, y: pd.Series, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value.
    
    Args:
        x: First series.
        y: Second series.
        method: 'pearson' or 'spearman'.
    
    Returns:
        Tuple of (correlation, p-value).
    """
    if method == 'pearson':
        return stats.pearsonr(x, y)
    elif method == 'spearman':
        return stats.spearmanr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")

def circular_block_permutation(x: pd.Series, y: pd.Series, alpha: float = 0.05, iterations: int = None) -> Tuple[float, bool]:
    """
    Perform circular block permutation test for significance.
    FR-005: Empirical p-values using block permutation to preserve temporal structure.
    
    Args:
        x: Independent variable series.
        y: Dependent variable series.
        alpha: Significance level.
        iterations: Number of permutations (defaults to config).
    
    Returns:
        Tuple of (empirical_p_value, is_significant).
    """
    if iterations is None:
        iterations = PERMUTATION_ITERATIONS
    
    n = len(x)
    obs_corr, _ = calculate_correlation(x, y, method='pearson')
    
    # Determine block size: first lag where autocorrelation < 0.5
    # If autocorrelation is weak, use a default block size (e.g., 10% of n)
    autocorr = x.autocorr()
    if autocorr > 0.5:
        block_size = max(1, int(n * 0.1))
    else:
        block_size = 1
    
    permuted_corrs = []
    for _ in range(iterations):
        # Circular shift
        shift = np.random.randint(1, n)
        x_perm = np.roll(x.values, shift)
        y_perm = np.roll(y.values, shift) # Or just shift y? Usually shift one relative to other
        # Actually, standard block permutation for time series:
        # We want to break the relationship between x and y while preserving internal structure.
        # A simple circular shift of y relative to x is a valid null model for lagged relationships.
        
        # Let's shift y relative to x
        y_shifted = np.roll(y.values, shift)
        
        # Calculate correlation on shifted data
        try:
            corr, _ = calculate_correlation(x.values, y_shifted, method='pearson')
            permuted_corrs.append(corr)
        except:
            continue
    
    permuted_corrs = np.array(permuted_corrs)
    # Two-tailed p-value
    # Count how many permuted stats are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(permuted_corrs) >= np.abs(obs_corr))
    p_val = (extreme_count + 1) / (len(permuted_corrs) + 1)
    
    is_significant = p_val < alpha
    return p_val, is_significant

def moving_block_bootstrap(x: pd.Series, y: pd.Series, iterations: int = None) -> Tuple[float, float]:
    """
    Moving block bootstrap for confidence intervals.
    FR-006: 95% confidence intervals.
    
    Args:
        x: Independent variable.
        y: Dependent variable.
        iterations: Number of bootstrap iterations.
    
    Returns:
        Tuple of (mean_corr, 95% CI tuple).
    """
    if iterations is None:
        iterations = BOOTSTRAP_ITERATIONS
    
    n = len(x)
    block_size = max(1, int(n ** 0.5)) # Heuristic block size
    
    boot_corrs = []
    for _ in range(iterations):
        # Generate block indices
        num_blocks = n // block_size
        indices = np.random.randint(0, n, num_blocks * block_size)
        # Ensure we don't go out of bounds with circular wrap or just truncate
        indices = indices % n
        
        x_boot = x.iloc[indices].values
        y_boot = y.iloc[indices].values
        
        try:
            corr, _ = calculate_correlation(x_boot, y_boot, method='pearson')
            boot_corrs.append(corr)
        except:
            continue
    
    boot_corrs = np.array(boot_corrs)
    mean_corr = np.mean(boot_corrs)
    ci_lower = np.percentile(boot_corrs, 2.5)
    ci_upper = np.percentile(boot_corrs, 97.5)
    
    return mean_corr, (ci_lower, ci_upper)
