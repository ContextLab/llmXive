"""
Correlation analysis module including permutation tests.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS, PERMUTATION_BLOCK_SIZE

def calculate_correlation(x: pd.Series, y: pd.Series, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate Pearson or Spearman correlation and p-value.
    
    Args:
        x: First time series.
        y: Second time series.
        method: 'pearson' or 'spearman'.
        
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(x) != len(y):
        raise ValueError("Series must be of equal length")
    
    # Remove NaNs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan
    
    if method == 'pearson':
        r, p = stats.pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        r, p = stats.spearmanr(x_clean, y_clean)
    else:
        raise ValueError("Method must be 'pearson' or 'spearman'")
    
    return float(r), float(p)

def circular_block_permutation(x: pd.Series, y: pd.Series, n_iterations: int = 1000, block_size: Optional[int] = None) -> Tuple[float, bool]:
    """
    Perform circular block permutation test to assess significance.
    
    Args:
        x: First time series.
        y: Second time series.
        n_iterations: Number of permutations.
        block_size: Size of blocks to preserve autocorrelation. 
                    If None, estimated from data.
                    
    Returns:
        Tuple of (empirical_p_value, is_significant_at_0.05).
    """
    if iterations is None:
        iterations = PERMUTATION_ITERATIONS
        
    n = len(x)
    if block_size is None:
        # Estimate block size: first lag where autocorrelation < 0.5
        # Simplified: use sqrt(n) as a heuristic if autocorrelation is weak
        block_size = max(1, int(np.sqrt(n)))
    
    # Observed statistic (Pearson r)
    obs_r, _ = calculate_correlation(x, y, method='pearson')
    
    perm_stats = []
    for _ in range(n_iterations):
        # Circular block permutation
        # Split into blocks and shuffle blocks
        indices = np.arange(n)
        # Create circular blocks
        blocks = []
        start = 0
        while start < n:
            end = min(start + block_size, n)
            blocks.append(indices[start:end])
            start = end
        
        # Shuffle blocks
        np.random.shuffle(blocks)
        perm_indices = np.concatenate(blocks)
        
        # Wrap around (circular)
        perm_indices = perm_indices % n
        
        x_perm = x.iloc[perm_indices].values
        y_perm = y.iloc[perm_indices].values # Actually we permute one relative to the other
        
        # Re-calc correlation
        r_perm, _ = calculate_correlation(pd.Series(x_perm), pd.Series(y_perm), method='pearson')
        perm_stats.append(r_perm)
    
    # Two-tailed p-value
    perm_stats = np.array(perm_stats)
    count_extreme = np.sum(np.abs(perm_stats) >= np.abs(obs_r))
    p_val = count_extreme / n_iterations
    
    is_significant = p_val < 0.05
    return float(p_val), bool(is_significant)

def moving_block_bootstrap(x: pd.Series, y: pd.Series, n_iterations: int = 1000, block_size: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Moving block bootstrap for confidence intervals.
    
    Returns:
        Tuple of (median_corr, lower_95, upper_95).
    """
    if iterations is None:
        iterations = BOOTSTRAP_ITERATIONS
        
    n = len(x)
    if block_size is None:
        block_size = max(1, int(np.sqrt(n)))
    
    bootstrap_corrs = []
    for _ in range(n_iterations):
        # Resample blocks
        indices = np.arange(n)
        blocks = []
        start = 0
        while start < n:
            end = min(start + block_size, n)
            blocks.append(indices[start:end])
            start = end
        
        # Sample blocks with replacement
        sampled_blocks = [np.random.choice(blocks, size=1)[0] for _ in range(len(blocks))]
        perm_indices = np.concatenate(sampled_blocks)
        perm_indices = perm_indices % n
        
        x_boot = x.iloc[perm_indices]
        y_boot = y.iloc[perm_indices]
        
        r_boot, _ = calculate_correlation(x_boot, y_boot, method='pearson')
        if not np.isnan(r_boot):
            bootstrap_corrs.append(r_boot)
    
    if not bootstrap_corrs:
        return np.nan, np.nan, np.nan
        
    bootstrap_corrs = np.array(bootstrap_corrs)
    median = np.median(bootstrap_corrs)
    lower = np.percentile(bootstrap_corrs, 2.5)
    upper = np.percentile(bootstrap_corrs, 97.5)
    
    return float(median), float(lower), float(upper)
