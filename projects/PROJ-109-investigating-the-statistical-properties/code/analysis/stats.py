"""
Statistical hypothesis testing and analysis (T031-T036).
Implements KS tests, Spearman correlations, and Benjamini-Hochberg correction.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

from utils.logging import get_logger
from config import ALPHA_THRESHOLD, BH_CORRECTION_METHOD

logger = get_logger(__name__)

def mass_binning(
    df: pd.DataFrame,
    mass_col: str = 'halo_mass',
    bins: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Bin halos by mass spanning multiple orders of magnitude.
    
    Args:
        df: Input DataFrame.
        mass_col: Column name for mass.
        bins: Custom bin edges. If None, uses log-spaced bins.
        
    Returns:
        DataFrame with 'mass_bin' column.
    """
    if bins is None:
        min_mass = df[mass_col].min()
        max_mass = df[mass_col].max()
        # Create 5 bins spanning the range
        bins = np.logspace(np.log10(min_mass), np.log10(max_mass), num=6)
    
    df = df.copy()
    df['mass_bin'] = pd.cut(df[mass_col], bins=bins, labels=False)
    return df

def environment_binning(
    df: pd.DataFrame,
    overdensity_col: str = 'local_overdensity',
    threshold: float = 200.0
) -> pd.DataFrame:
    """
    Bin halos by environment (low vs high overdensity).
    
    Args:
        df: Input DataFrame.
        overdensity_col: Column name for overdensity.
        threshold: Threshold for high environment (default 200).
        
    Returns:
        DataFrame with 'env_bin' column (0: low, 1: high).
    """
    df = df.copy()
    df['env_bin'] = (df[overdensity_col] >= threshold).astype(int)
    return df

def run_ks_tests(
    df: pd.DataFrame,
    metrics: List[str],
    group_col: str = 'env_bin',
    groups: List[int] = [0, 1]
) -> Dict[str, Any]:
    """
    Perform two-sample KS tests between environmental bins for each metric.
    
    Args:
        df: Input DataFrame.
        metrics: List of metric columns to test.
        group_col: Column name for grouping.
        groups: List of group labels to compare.
        
    Returns:
        Dictionary of KS test results.
    """
    results = {}
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found, skipping KS test.")
            continue
        
        # Filter for valid groups
        mask = df[group_col].isin(groups)
        if mask.sum() < 2:
            logger.warning(f"Not enough data points for KS test on {metric}.")
            continue
        
        group_data = {g: df.loc[df[group_col] == g, metric].dropna() for g in groups}
        
        # Check if we have data in both groups
        if any(len(gd) < 2 for gd in group_data.values()):
            logger.warning(f"Insufficient data for KS test on {metric}.")
            continue
        
        stat, pvalue = stats.ks_2samp(group_data[groups[0]], group_data[groups[1]])
        results[metric] = {
            'statistic': float(stat),
            'pvalue': float(pvalue),
            'n1': len(group_data[groups[0]]),
            'n2': len(group_data[groups[1]])
        }
    
    return results

def apply_benjamini_hochberg(
    pvalues: List[float],
    alpha: float = ALPHA_THRESHOLD,
    method: str = BH_CORRECTION_METHOD
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg correction for multiple hypothesis testing.
    
    Args:
        pvalues: List of raw p-values.
        alpha: Significance threshold.
        method: Correction method (currently only 'bh' supported).
        
    Returns:
        Tuple of (adjusted p-values, boolean mask of significant tests).
    """
    if method != 'bh':
        logger.warning(f"Method {method} not implemented, defaulting to 'bh'.")
        method = 'bh'
    
    # Use scipy's multipletests if available, else implement manually
    try:
        from statsmodels.stats.multitest import multipletests
        reject, pvals_corrected, _, _ = multipletests(pvalues, alpha=alpha, method=method)
    except ImportError:
        # Fallback implementation
        n = len(pvalues)
        if n == 0:
            return [], []
        
        # Sort p-values and track original indices
        sorted_indices = np.argsort(pvalues)
        sorted_pvals = np.array(pvalues)[sorted_indices]
        
        # Calculate adjusted p-values
        adjusted = np.zeros(n)
        for i in range(n):
            # BH formula: p_adj = p * n / rank
            # Ensure non-decreasing
            rank = i + 1
            adj_val = sorted_pvals[i] * n / rank
            adj_val = min(adj_val, 1.0)
            adjusted[i] = adj_val
        
        # Make non-decreasing from the end
        for i in range(n - 2, -1, -1):
            adjusted[i] = min(adjusted[i], adjusted[i + 1])
        
        pvals_corrected = np.zeros(n)
        pvals_corrected[sorted_indices] = adjusted
        
        reject = pvals_corrected < alpha
    
    return list(pvals_corrected), list(reject)

def run_spearman_correlations(
    df: pd.DataFrame,
    mass_col: str = 'halo_mass',
    metrics: List[str] = ['shape_s', 'spin_lambda', 'concentration_c']
) -> Dict[str, Any]:
    """
    Compute Spearman's rho between halo mass and each metric.
    
    Args:
        df: Input DataFrame.
        mass_col: Column name for mass.
        metrics: List of metric columns.
        
    Returns:
        Dictionary of correlation results.
    """
    results = {}
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        # Drop NaNs
        valid_data = df[[mass_col, metric]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Insufficient data for correlation on {metric}.")
            continue
        
        rho, pvalue = stats.spearmanr(valid_data[mass_col], valid_data[metric])
        results[metric] = {
            'rho': float(rho),
            'pvalue': float(pvalue),
            'n': len(valid_data)
        }
    
    return results

def bullock_comparison(
    df: pd.DataFrame,
    mass_col: str = 'halo_mass',
    concentration_col: str = 'concentration_c',
    c_200: float = 10.0,
    alpha: float = -0.1
) -> Dict[str, Any]:
    """
    Compare observed concentrations to Bullock et al. (2001) analytic fit.
    
    c(M) = c_200 * (M / M_200)^alpha
    
    Args:
        df: Input DataFrame.
        mass_col: Column name for mass.
        concentration_col: Column name for concentration.
        c_200: Normalization constant.
        alpha: Power law slope.
        
    Returns:
        Dictionary with deviation statistics.
    """
    # Normalize mass by a reference M_200 (e.g., 1e14 Msun)
    M_ref = 1e14
    M_norm = df[mass_col] / M_ref
    
    # Predicted concentration
    c_pred = c_200 * (M_norm ** alpha)
    
    # Calculate deviations
    observed = df[concentration_col].dropna()
    predicted = c_pred.loc[observed.index]
    
    if len(observed) == 0:
        return {'error': 'No data available'}
    
    residuals = observed - predicted
    mean_res = float(np.mean(residuals))
    std_res = float(np.std(residuals))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    
    return {
        'c_200': c_200,
        'alpha': alpha,
        'mean_residual': mean_res,
        'std_residual': std_res,
        'rmse': rmse,
        'n_points': len(observed)
    }

def run_full_analysis_pipeline(
    df: pd.DataFrame,
    output_path: str,
    figures_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete statistical analysis pipeline.
    
    Args:
        df: Input DataFrame with metrics and mass.
        output_path: Path to save results JSON.
        figures_dir: Directory to save figures.
        
    Returns:
        Dictionary of all results.
    """
    results = {}
    
    # 1. Binning
    df_binned = mass_binning(df)
    df_binned = environment_binning(df_binned)
    results['binning'] = {
        'mass_bins': int(df_binned['mass_bin'].nunique()),
        'env_bins': int(df_binned['env_bin'].nunique())
    }
    
    # 2. KS Tests
    metrics = ['shape_s', 'spin_lambda', 'concentration_c']
    ks_results = run_ks_tests(df_binned, metrics)
    results['ks_tests'] = ks_results
    
    # 3. BH Correction
    pvalues = [res['pvalue'] for res in ks_results.values()]
    if pvalues:
        adj_pvals, significant = apply_benjamini_hochberg(pvalues)
        results['bh_correction'] = {
            'adjusted_pvalues': adj_pvals,
            'significant': significant,
            'threshold': ALPHA_THRESHOLD
        }
    
    # 4. Spearman Correlations
    spearman_results = run_spearman_correlations(df_binned)
    results['spearman_correlations'] = spearman_results
    
    # 5. Bullock Comparison
    bullock_res = bullock_comparison(df_binned)
    results['bullock_comparison'] = bullock_res
    
    # 6. Save Results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved analysis results to {output_path}")
    
    # 7. Generate Figures
    if figures_dir:
        from analysis.visualize import generate_all_visualizations
        generate_all_visualizations(df_binned, figures_dir)
    
    return results