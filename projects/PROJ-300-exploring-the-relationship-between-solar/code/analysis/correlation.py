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
        x: First array.
        y: Second array.
        method: 'pearson' or 'spearman'.
    
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if method == 'pearson':
        corr, p_val = stats.pearsonr(x, y)
    elif method == 'spearman':
        corr, p_val = stats.spearmanr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(corr), float(p_val)

def circular_block_permutation(x: np.ndarray, y: np.ndarray, n_iterations: int = PERMUTATION_ITERATIONS, 
                               block_size: Optional[int] = None) -> float:
    """
    Perform circular block permutation test to estimate empirical p-value.
    
    Args:
        x: Independent variable array.
        y: Dependent variable array.
        n_iterations: Number of permutations.
        block_size: Size of blocks to preserve autocorrelation. 
                   If None, calculates based on autocorrelation decay.
    
    Returns:
        Empirical p-value.
    """
    n = len(x)
    if block_size is None:
        # Estimate block size: first lag where autocorrelation < 0.5
        autocorr = np.correlate(x - np.mean(x), x - np.mean(x), mode='full')
        autocorr = autocorr[n-1:] / autocorr[-1]
        # Find first index where autocorr < 0.5
        mask = autocorr < 0.5
        if np.any(mask):
            block_size = np.argmax(mask) + 1
        else:
            block_size = max(1, n // 10) # Default fallback
    
    block_size = min(block_size, n // 2)
    
    # Observed statistic
    obs_stat, _ = calculate_correlation(x, y, method='pearson')
    obs_stat = abs(obs_stat)
    
    count_extreme = 0
    
    for _ in range(n_iterations):
        # Circular shift blocks
        # Create blocks
        n_blocks = n // block_size
        if n_blocks == 0:
            n_blocks = 1
        
        # Generate random permutation of block indices
        block_indices = np.random.permutation(n_blocks)
        
        # Construct shuffled y
        y_shuffled = np.empty(n)
        current_idx = 0
        for i in range(n_blocks):
            block_start = i * block_size
            block_end = block_start + block_size
            if block_end > n: block_end = n
            
            # Map to shuffled block
            shuffled_block_idx = block_indices[i]
            src_start = shuffled_block_idx * block_size
            src_end = src_start + block_size
            if src_end > n: src_end = n
            
            y_shuffled[current_idx:current_idx + (block_end - block_start)] = y[src_start:src_end]
            current_idx += (block_end - block_start)
        
        # Handle remainder
        remainder = n - current_idx
        if remainder > 0:
            # Wrap around for circular
            src_start = (block_indices[-1] * block_size) + (block_end - block_start)
            if src_start >= n: src_start = 0
            y_shuffled[current_idx:] = y[src_start:src_start+remainder]
        
        # Calculate permuted statistic
        perm_stat, _ = calculate_correlation(x, y_shuffled, method='pearson')
        if abs(perm_stat) >= obs_stat:
            count_extreme += 1
    
    p_value = (count_extreme + 1) / (n_iterations + 1)
    return p_value

def moving_block_bootstrap(x: np.ndarray, y: np.ndarray, n_iterations: int = BOOTSTRAP_ITERATIONS,
                           block_size: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Moving block bootstrap for 95% confidence intervals.
    
    Args:
        x: Independent variable.
        y: Dependent variable.
        n_iterations: Number of bootstrap iterations.
        block_size: Block size for resampling.
    
    Returns:
        Tuple of (mean_correlation, lower_ci, upper_ci).
    """
    n = len(x)
    if block_size is None:
        block_size = max(1, n // 10)
    
    correlations = []
    
    for _ in range(n_iterations):
        # Resample blocks
        n_blocks = int(np.ceil(n / block_size))
        indices = np.random.randint(0, n, size=n_blocks) * block_size
        
        x_resampled = np.concatenate([x[i:i+block_size] for i in indices])[:n]
        y_resampled = np.concatenate([y[i:i+block_size] for i in indices])[:n]
        
        if len(x_resampled) == 0 or np.std(x_resampled) == 0 or np.std(y_resampled) == 0:
            continue
            
        r, _ = calculate_correlation(x_resampled, y_resampled, method='pearson')
        correlations.append(r)
    
    if not correlations:
        return 0.0, 0.0, 0.0
        
    corr_arr = np.array(correlations)
    mean_r = np.mean(corr_arr)
    lower = np.percentile(corr_arr, 2.5)
    upper = np.percentile(corr_arr, 97.5)
    
    return mean_r, lower, upper
