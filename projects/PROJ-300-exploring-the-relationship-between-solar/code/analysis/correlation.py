"""
code/analysis/correlation.py
Implements correlation metrics and statistical testing.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS


def calculate_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Calculate Pearson and Spearman correlation coefficients.
    
    Args:
        x: First time series.
        y: Second time series.
        
    Returns:
        Tuple of (pearson_r, spearman_r).
    """
    # Drop NaNs
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return 0.0, 0.0
        
    pearson_r, _ = stats.pearsonr(x_clean, y_clean)
    spearman_r, _ = stats.spearmanr(x_clean, y_clean)
    
    return pearson_r, spearman_r


def circular_block_permutation(
    x: pd.Series, 
    y: pd.Series, 
    iterations: int = PERMUTATION_ITERATIONS
) -> float:
    """
    Perform circular block permutation test to estimate empirical p-value.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of permutations.
        
    Returns:
        Empirical p-value.
    """
    mask = x.notna() & y.notna()
    x_clean = x[mask].values
    y_clean = y[mask].values
    
    n = len(x_clean)
    if n < 10:
        return 1.0
        
    # Calculate observed correlation
    obs_corr, _ = stats.pearsonr(x_clean, y_clean)
    obs_abs_corr = abs(obs_corr)
    
    # Estimate block size: first lag where autocorrelation < 0.5
    # Use a simple heuristic if autocorrelation is weak
    block_size = max(1, n // 10)
    try:
        acf = stats.acf(x_clean, nlags=min(20, n-1), fft=False)
        for i in range(1, len(acf)):
            if acf[i] < 0.5:
                block_size = max(1, i)
                break
    except:
        pass # Fallback to default
        
    block_size = min(block_size, n // 2)
    
    count_extreme = 0
    for _ in range(iterations):
        # Circular shift y
        shift = np.random.randint(1, n)
        y_perm = np.roll(y_clean, shift)
        
        # Calculate permuted correlation
        try:
            perm_corr, _ = stats.pearsonr(x_clean, y_perm)
            if abs(perm_corr) >= obs_abs_corr:
                count_extreme += 1
        except:
            continue
            
    p_value = (count_extreme + 1) / (iterations + 1)
    return p_value


def moving_block_bootstrap(
    x: pd.Series, 
    y: pd.Series, 
    iterations: int = BOOTSTRAP_ITERATIONS
) -> Tuple[float, float]:
    """
    Perform moving block bootstrap to estimate 95% confidence interval.
    
    Args:
        x: First time series.
        y: Second time series.
        iterations: Number of bootstrap iterations.
        
    Returns:
        Tuple of (lower_ci, upper_ci).
    """
    mask = x.notna() & y.notna()
    x_clean = x[mask].values
    y_clean = y[mask].values
    
    n = len(x_clean)
    if n < 20:
        return -1.0, 1.0
        
    # Estimate block size
    block_size = max(1, n // 10)
    try:
        acf = stats.acf(x_clean, nlags=min(20, n-1), fft=False)
        for i in range(1, len(acf)):
            if acf[i] < 0.5:
                block_size = max(1, i)
                break
    except:
        pass
        
    block_size = min(block_size, n // 2)
    n_blocks = int(np.ceil(n / block_size))
    
    bootstrap_corrs = []
    for _ in range(iterations):
        # Resample blocks
        indices = []
        for _ in range(n_blocks):
            start = np.random.randint(0, n - block_size + 1)
            indices.extend(range(start, start + block_size))
        
        # Truncate to original length
        indices = indices[:n]
        
        x_boot = x_clean[indices]
        y_boot = y_clean[indices]
        
        try:
            corr, _ = stats.pearsonr(x_boot, y_boot)
            bootstrap_corrs.append(corr)
        except:
            continue
            
    if len(bootstrap_corrs) == 0:
        return -1.0, 1.0
        
    lower = np.percentile(bootstrap_corrs, 2.5)
    upper = np.percentile(bootstrap_corrs, 97.5)
    
    return lower, upper
