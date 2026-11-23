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
        x: Series 1
        y: Series 2
        
    Returns:
        dict: {'pearson': float, 'spearman': float}
    """
    pearson_corr, _ = stats.pearsonr(x, y)
    spearman_corr, _ = stats.spearmanr(x, y)
    
    return {
        "pearson": pearson_corr,
        "spearman": spearman_corr
    }

def circular_block_permutation(x: pd.Series, y: pd.Series, n_iterations: int = 10000) -> float:
    """
    Perform circular block permutation test for empirical p-value.
    
    Args:
        x: Series 1
        y: Series 2
        n_iterations: Number of permutations
        
    Returns:
        float: Empirical p-value
    """
    n = len(x)
    block_size = PERMUTATION_BLOCK_SIZE
    
    # Calculate observed correlation
    obs_corr, _ = stats.pearsonr(x, y)
    obs_corr = abs(obs_corr)
    
    permuted_corrs = []
    
    for _ in range(n_iterations):
        # Circular shift
        shift = np.random.randint(1, n)
        x_perm = np.roll(x.values, shift)
        
        # Calculate permuted correlation
        perm_corr, _ = stats.pearsonr(x_perm, y)
        permuted_corrs.append(abs(perm_corr))
        
    # Calculate p-value
    p_val = np.mean([pc >= obs_corr for pc in permuted_corrs])
    
    logger.debug(f"Permutation test p-value: {p_val:.4f}")
    return p_val

def moving_block_bootstrap(x: pd.Series, y: pd.Series, n_iterations: int = 1000) -> Tuple[float, float]:
    """
    Perform moving block bootstrap for 95% confidence intervals.
    
    Args:
        x: Series 1
        y: Series 2
        n_iterations: Number of bootstrap iterations
        
    Returns:
        tuple: (ci_lower, ci_upper)
    """
    n = len(x)
    block_size = PERMUTATION_BLOCK_SIZE
    num_blocks = int(np.ceil(n / block_size))
    
    bootstrap_corrs = []
    
    for _ in range(n_iterations):
        # Resample blocks
        indices = np.random.randint(0, n - block_size + 1, num_blocks)
        block_indices = []
        for idx in indices:
            block_indices.extend(range(idx, min(idx + block_size, n)))
        
        block_indices = block_indices[:n] # Truncate to original length
        
        x_boot = x.iloc[block_indices].values
        y_boot = y.iloc[block_indices].values
        
        # Calculate correlation
        corr, _ = stats.pearsonr(x_boot, y_boot)
        bootstrap_corrs.append(corr)
        
    ci_lower = np.percentile(bootstrap_corrs, 2.5)
    ci_upper = np.percentile(bootstrap_corrs, 97.5)
    
    logger.debug(f"Bootstrap CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    return ci_lower, ci_upper
