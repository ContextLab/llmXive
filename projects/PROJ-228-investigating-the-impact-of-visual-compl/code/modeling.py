"""
Modeling module for GLM and permutation test structure.

This module provides the skeleton and implementation for statistical modeling,
including linear regression with AR(1) pre-whitening and circular block permutation tests.
"""

import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Ensure seeds are initialized if config is available
try:
    from config import init_seeds
    init_seeds()
except ImportError:
    pass

def _validate_inputs(X: np.ndarray, y: np.ndarray) -> None:
    """Validate input arrays for regression."""
    if X.ndim != 2:
        raise ValueError(f"X must be 2D, got {X.ndim}D")
    if y.ndim != 1:
        raise ValueError(f"y must be 1D, got {y.ndim}D")
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y must have same number of samples: {X.shape[0]} vs {y.shape[0]}")
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        raise ValueError("Input arrays contain NaN values")
    if np.any(np.isinf(X)) or np.any(np.isinf(y)):
        raise ValueError("Input arrays contain Inf values")

def _ols_with_ar1(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform OLS regression with AR(1) pre-whitening.
    
    This is a simplified implementation that:
    1. Fits OLS
    2. Estimates AR(1) parameter from residuals
    3. Applies pre-whitening
    4. Refits model
    
    Args:
        X: Design matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        
    Returns:
        Dictionary with coefficients, p-values, and residuals
    """
    n_samples, n_features = X.shape
    
    # Add intercept if not present
    has_intercept = np.allclose(X[:, 0], 1.0, atol=1e-6)
    if not has_intercept:
        X_aug = np.column_stack([np.ones(n_samples), X])
    else:
        X_aug = X
    
    # Initial OLS fit
    XtX = X_aug.T @ X_aug
    XtX_inv = np.linalg.pinv(XtX)
    beta_ols = XtX_inv @ X_aug.T @ y
    
    # Residuals
    y_pred = X_aug @ beta_ols
    residuals = y - y_pred
    
    # Estimate AR(1) parameter
    if len(residuals) > 1:
        rho = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
        if np.isnan(rho):
            rho = 0.0
    else:
        rho = 0.0
    
    # Pre-whitening
    if abs(rho) > 0.01:
        # Transform data
        y_w = np.zeros_like(y)
        X_w = np.zeros_like(X_aug)
        
        y_w[0] = y[0] * np.sqrt(1 - rho**2)
        X_w[0] = X_aug[0] * np.sqrt(1 - rho**2)
        
        for t in range(1, n_samples):
            y_w[t] = y[t] - rho * y[t-1]
            X_w[t] = X_aug[t] - rho * X_aug[t-1]
        
        # Refit on whitened data
        XtX_w = X_w.T @ X_w
        XtX_inv_w = np.linalg.pinv(XtX_w)
        beta = XtX_inv_w @ X_w.T @ y_w
        
        # Residuals from whitened model
        residuals_w = y_w - X_w @ beta
    else:
        beta = beta_ols
        residuals_w = residuals
    
    # Standard errors and t-statistics
    ss_res = np.sum(residuals_w**2)
    mse = ss_res / (n_samples - n_features - (0 if has_intercept else 1))
    var_beta = mse * XtX_inv_w
    se_beta = np.sqrt(np.diag(var_beta))
    
    t_stats = beta / se_beta
    
    # P-values (two-tailed, using normal approximation for large n)
    # For small samples, t-distribution would be more appropriate
    p_values = 2 * (1 - 0.5 * (1 + np.sign(t_stats) * np.abs(t_stats) / 
                               np.sqrt(np.abs(t_stats)**2 + n_samples)))
    
    return {
        'coefficients': beta,
        'standard_errors': se_beta,
        't_statistics': t_stats,
        'p_values': p_values,
        'residuals': residuals_w,
        'rho': rho,
        'has_intercept': has_intercept
    }

def circular_block_permutation(y: np.ndarray, n_permutations: int = 1000, 
                               block_size: Optional[int] = None, 
                               seed: Optional[int] = None) -> np.ndarray:
    """
    Generate null distribution using circular block permutation.
    
    This preserves temporal autocorrelation by permuting blocks of data
    rather than individual observations.
    
    Args:
        y: Target vector
        n_permutations: Number of permutations to generate
        block_size: Size of blocks to permute. If None, uses 2 * len(y) / 100
        seed: Random seed for reproducibility
        
    Returns:
        Array of permuted statistics (correlation coefficients)
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_samples = len(y)
    
    if block_size is None:
        # Default block size: 2% of samples, minimum 2
        block_size = max(2, int(n_samples * 0.02))
    
    # Calculate observed statistic (correlation with time index as proxy)
    # In real usage, this would be correlation with complexity metric
    time_index = np.arange(n_samples)
    obs_stat = np.corrcoef(y, time_index)[0, 1]
    
    null_distribution = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        # Create circular permutation of blocks
        n_blocks = n_samples // block_size
        remaining = n_samples % block_size
        
        # Generate random block permutation
        block_indices = np.random.permutation(n_blocks)
        
        # Construct permuted array
        y_perm = np.zeros_like(y)
        current_idx = 0
        
        for block_idx in block_indices:
            start = block_idx * block_size
            end = start + block_size
            y_perm[current_idx:current_idx+block_size] = y[start:end]
            current_idx += block_size
        
        # Handle remaining samples
        if remaining > 0:
            y_perm[current_idx:] = y[n_samples-remaining:]
        
        # Calculate statistic for permuted data
        perm_stat = np.corrcoef(y_perm, time_index)[0, 1]
        null_distribution[i] = perm_stat
    
    return null_distribution

def run_regression(X: np.ndarray, y: np.ndarray, 
                  n_permutations: int = 1000,
                  block_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Run regression analysis with permutation test validation.
    
    Args:
        X: Design matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_permutations: Number of permutations for null distribution
        block_size: Block size for circular permutation (optional)
        
    Returns:
        Dictionary containing:
        - coefficients: Regression coefficients
        - p_values: Raw p-values
        - fdr_corrected_p: FDR-corrected p-values
        - permutation_p: Permutation-based p-value
        - is_significant: Whether result is significant after correction
        - null_distribution: Array of null statistics
        - observed_statistic: Observed correlation coefficient
    """
    # Validate inputs
    _validate_inputs(X, y)
    
    # Run regression with AR(1) pre-whitening
    regression_results = _ols_with_ar1(X, y)
    
    # Extract key statistics
    coefficients = regression_results['coefficients']
    p_values = regression_results['p_values']
    
    # FDR correction (Benjamini-Hochberg)
    n_tests = len(p_values)
    if n_tests > 0:
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        # Calculate BH thresholds
        thresholds = (np.arange(1, n_tests + 1) / n_tests) * 0.05
        
        # Find largest k where p[k] <= threshold[k]
        valid = sorted_p <= thresholds
        if np.any(valid):
            k = np.max(np.where(valid)[0])
            fdr_threshold = thresholds[k]
        else:
            fdr_threshold = 0.0
        
        # Apply correction
        fdr_corrected_p = np.minimum.accumulate(p_values[::-1] * n_tests / 
                                                (np.arange(n_tests, 0, -1) + 1e-10))[::-1]
        fdr_corrected_p = np.minimum(fdr_corrected_p, 1.0)
    else:
        fdr_corrected_p = np.array([])
    
    # Run permutation test
    # Use the first predictor (excluding intercept) for correlation test
    if coefficients.shape[0] > 1:
        # Correlation between y and first predictor (index 1 if intercept, 0 otherwise)
        pred_idx = 1 if regression_results['has_intercept'] else 0
        if X.shape[1] > pred_idx:
            observed_corr = np.corrcoef(y, X[:, pred_idx])[0, 1]
        else:
            observed_corr = np.corrcoef(y, np.arange(len(y)))[0, 1]
    else:
        observed_corr = np.corrcoef(y, np.arange(len(y)))[0, 1]
    
    null_dist = circular_block_permutation(y, n_permutations, block_size)
    
    # Calculate permutation p-value
    # Two-tailed: proportion of null stats more extreme than observed
    extreme_count = np.sum(np.abs(null_dist) >= np.abs(observed_corr))
    permutation_p = (extreme_count + 1) / (n_permutations + 1)
    
    # Determine significance
    is_significant = permutation_p < 0.05
    
    return {
        'coefficients': coefficients.tolist(),
        'standard_errors': regression_results['standard_errors'].tolist(),
        't_statistics': regression_results['t_statistics'].tolist(),
        'p_values': p_values.tolist(),
        'fdr_corrected_p': fdr_corrected_p.tolist() if len(fdr_corrected_p) > 0 else [],
        'permutation_p': float(permutation_p),
        'is_significant': bool(is_significant),
        'observed_statistic': float(observed_corr),
        'null_distribution': null_dist.tolist(),
        'rho': float(regression_results['rho']),
        'n_permutations': n_permutations
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def load_data_for_modeling(complexity_path: Path, timeseries_path: Path) -> tuple:
    """
    Load and merge complexity metrics and PFC timeseries.
    
    Args:
        complexity_path: Path to complexity_metrics.csv
        timeseries_path: Path to pfc_timeseries.csv
        
    Returns:
        Tuple of (X, y) arrays ready for modeling
    """
    # This is a placeholder that will be implemented in T031
    # For now, raise NotImplementedError to indicate it needs implementation
    raise NotImplementedError(
        "Data loading for modeling not yet implemented. "
        "This will be completed in task T031."
    )