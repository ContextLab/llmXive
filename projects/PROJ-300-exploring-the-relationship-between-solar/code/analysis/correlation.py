"""
Correlation analysis module including permutation tests and bootstrap.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS, PERMUTATION_BLOCK_SIZE

def calculate_correlation(x: np.ndarray, y: np.ndarray, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate Pearson or Spearman correlation and p-value.
    
    Args:
        x: First time series.
        y: Second time series.
        method: 'pearson' or 'spearman'.
        
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(x) < 2 or len(y) < 2:
        return 0.0, 1.0
        
    # Handle NaNs
    valid = ~(x.isna() | y.isna())
    x_clean = x[valid]
    y_clean = y[valid]
    
    if len(x_clean) < 2:
        return 0.0, 1.0
        
    if method == 'spearman':
        corr, pval = stats.spearmanr(x_clean, y_clean)
    else:
        corr, pval = stats.pearsonr(x_clean, y_clean)
        
    return float(corr), float(pval)

def circular_block_permutation(x: pd.Series, y: pd.Series, iterations: Optional[int] = None) -> float:
    """
    Perform circular block permutation test to estimate empirical p-value.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of permutations (defaults to PERMUTATION_ITERATIONS from config).
        
    Returns:
        Empirical p-value.
    """
    if iterations is None:
        iterations = PERMUTATION_ITERATIONS
        
    n = len(x)
    if n < 10:
        return 1.0
        
    # Calculate observed statistic
    obs_corr, _ = calculate_correlation(x, y, method='pearson')
    obs_stat = abs(obs_corr)
    
    # Determine block size: first lag where autocorrelation < 0.5
    # Simple heuristic: use sqrt(n) or a fixed minimum if autocorrelation is weak
    block_size = max(1, int(np.sqrt(n)))
    
    count_extreme = 0
    for _ in range(iterations):
        # Circular block permutation
        # Split into blocks of size 'block_size'
        num_blocks = n // block_size
        remainder = n % block_size
        
        # Create a shuffled index using circular blocks
        indices = np.arange(n)
        block_indices = np.arange(0, num_blocks * block_size, block_size)
        
        # Shuffle block start positions
        np.random.shuffle(block_indices)
        
        # Reconstruct permutation
        permuted_indices = []
        current_idx = 0
        for start in block_indices:
            end = start + block_size
            permuted_indices.extend(indices[start:end])
            current_idx = end
        
        # Handle remainder
        if remainder > 0:
            permuted_indices.extend(indices[num_blocks * block_size:])
        
        permuted_y = y.iloc[permuted_indices].reset_index(drop=True)
        x_aligned = x.reset_index(drop=True)
        
        perm_corr, _ = calculate_correlation(x_aligned, permuted_y, method='pearson')
        if abs(perm_corr) >= obs_stat:
            count_extreme += 1
            
    p_value = (count_extreme + 1) / (iterations + 1)
    return float(p_value)

def moving_block_bootstrap(x: pd.Series, y: pd.Series, iterations: Optional[int] = None) -> Tuple[float, float]:
    """
    Perform moving block bootstrap to estimate 95% confidence intervals.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of bootstrap iterations (defaults to BOOTSTRAP_ITERATIONS from config).
        
    Returns:
        Tuple of (mean_correlation, confidence_interval_width).
    """
    if iterations is None:
        iterations = BOOTSTRAP_ITERATIONS
        
    n = len(x)
    if n < 10:
        return 0.0, 0.0
        
    block_size = max(1, int(np.sqrt(n)))
    n_blocks = n // block_size
    
    correlations = []
    for _ in range(iterations):
        # Resample blocks
        bootstrap_indices = []
        for _ in range(n_blocks):
            start = np.random.randint(0, n - block_size)
            bootstrap_indices.extend(range(start, start + block_size))
        
        # Handle remainder
        if len(bootstrap_indices) < n:
            bootstrap_indices.extend(range(len(bootstrap_indices), n))
        
        bootstrap_indices = bootstrap_indices[:n]
        
        x_boot = x.iloc[bootstrap_indices].reset_index(drop=True)
        y_boot = y.iloc[bootstrap_indices].reset_index(drop=True)
        
        corr, _ = calculate_correlation(x_boot, y_boot, method='pearson')
        correlations.append(corr)
        
    mean_corr = np.mean(correlations)
    ci_lower = np.percentile(correlations, 2.5)
    ci_upper = np.percentile(correlations, 97.5)
    ci_width = ci_upper - ci_lower
    
    return float(mean_corr), float(ci_width)
