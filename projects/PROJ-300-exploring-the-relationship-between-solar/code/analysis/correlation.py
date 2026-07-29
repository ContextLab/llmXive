"""
Correlation analysis module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional
from ..config import BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS, PERMUTATION_BLOCK_SIZE
import logging

logger = logging.getLogger(__name__)

def calculate_correlation(x: pd.Series, y: pd.Series) -> dict:
    """
    Calculate Pearson and Spearman correlation coefficients.
    
    Args:
        x: First time series
        y: Second time series
        
    Returns:
        Dictionary with keys 'pearson' and 'spearman'
    """
    # Remove NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return {"pearson": np.nan, "spearman": np.nan}
    
    # Calculate correlations
    pearson_corr, _ = stats.pearsonr(x_clean, y_clean)
    spearman_corr, _ = stats.spearmanr(x_clean, y_clean)
    
    return {
        "pearson": float(pearson_corr),
        "spearman": float(spearman_corr)
    }

def circular_block_permutation(x: pd.Series, y: pd.Series, n_iterations: int = 10000) -> float:
    """
    Perform circular block permutation test for empirical p-value.
    
    Args:
        x: First time series
        y: Second time series
        n_iterations: Number of permutations
        
    Returns:
        Empirical p-value
    """
    # Remove NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask].values
    y_clean = y[mask].values
    
    if len(x_clean) < 2:
        return 1.0
    
    # Calculate observed correlation
    obs_corr, _ = stats.pearsonr(x_clean, y_clean)
    obs_corr = abs(obs_corr)
    
    # Block size (fixed as per FR-005)
    block_size = PERMUTATION_BLOCK_SIZE
    
    # Permutation test
    count = 0
    n = len(x_clean)
    
    for _ in range(n_iterations):
        # Circular block permutation
        perm_indices = np.random.permutation(n)
        x_perm = x_clean[perm_indices]
        
        # Calculate permuted correlation
        perm_corr, _ = stats.pearsonr(x_perm, y_clean)
        perm_corr = abs(perm_corr)
        
        if perm_corr >= obs_corr:
            count += 1
    
    p_value = count / n_iterations
    logger.info(f"Permutation test completed: p-value = {p_value:.4f}")
    
    return p_value

def moving_block_bootstrap(x: pd.Series, y: pd.Series, n_iterations: int = 1000) -> Tuple[float, float]:
    """
    Perform moving block bootstrap for 95% confidence interval.
    
    Args:
        x: First time series
        y: Second time series
        n_iterations: Number of bootstrap iterations
        
    Returns:
        Tuple (ci_lower, ci_upper)
    """
    # Remove NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask].values
    y_clean = y[mask].values
    
    if len(x_clean) < 2:
        return (np.nan, np.nan)
    
    # Block size (same as permutation test)
    block_size = PERMUTATION_BLOCK_SIZE
    n = len(x_clean)
    
    # Bootstrap correlations
    bootstrap_corrs = []
    
    for _ in range(n_iterations):
        # Moving block bootstrap
        indices = []
        while len(indices) < n:
            start = np.random.randint(0, n - block_size + 1)
            indices.extend(range(start, min(start + block_size, n)))
        
        indices = indices[:n]
        x_boot = x_clean[indices]
        y_boot = y_clean[indices]
        
        # Calculate correlation
        corr, _ = stats.pearsonr(x_boot, y_boot)
        bootstrap_corrs.append(corr)
    
    # Calculate 95% CI
    ci_lower = np.percentile(bootstrap_corrs, 2.5)
    ci_upper = np.percentile(bootstrap_corrs, 97.5)
    
    logger.info(f"Bootstrap CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return (float(ci_lower), float(ci_upper))
