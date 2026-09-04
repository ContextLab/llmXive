import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from config import RHO_CRITICAL, ENVIRONMENT_THRESHOLD, BULLOCK_C200, BULLOCK_ALPHA, BH_THRESHOLD
from utils.logging import get_logger

logger = get_logger(__name__)

def mass_binning(df: pd.DataFrame, column: str = "mass", bins: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Bin halos by mass across multiple orders of magnitude.
    
    Args:
        df: DataFrame containing halo data.
        column: Name of the mass column.
        bins: List of bin edges. If None, generates logarithmic bins.
    
    Returns:
        DataFrame with an added 'mass_bin' column.
    """
    if bins is None:
        # Generate logarithmic bins spanning typical halo masses
        # Assuming mass is in Msun/h
        min_mass = df[column].min()
        max_mass = df[column].max()
        if min_mass <= 0 or max_mass <= 0:
            raise ValueError("Mass values must be positive for logarithmic binning.")
        n_bins = int(np.log10(max_mass) - np.log10(min_mass)) + 5
        bins = np.logspace(np.log10(min_mass), np.log10(max_mass), n_bins)
    
    logger.info(f"Creating {len(bins)-1} mass bins from {min(bins):.2e} to {max(bins):.2e}")
    df = df.copy()
    df['mass_bin'] = pd.cut(df[column], bins=bins, labels=False)
    return df

def environment_binning(df: pd.DataFrame, overdensity_col: str = "overdensity") -> pd.DataFrame:
    """
    Bin halos by environment using overdensity relative to critical density.
    
    Requirement: Explicitly use RHO_CRITICAL from code/config.py for overdensity normalization.
    Environment bins: Δ < 200 vs Δ ≥ 200.
    
    Args:
        df: DataFrame containing halo data.
        overdensity_col: Name of the column containing local overdensity values (Δ).
    
    Returns:
        DataFrame with an added 'environment_bin' column (0 for low, 1 for high).
    """
    if overdensity_col not in df.columns:
        # If overdensity is not pre-calculated, we might need to compute it or assume
        # the column exists based on US1/US2 pipeline. For this task, we assume it exists.
        logger.warning(f"Column '{overdensity_col}' not found. Attempting to normalize raw density if 'density' exists.")
        if "density" in df.columns:
            # Normalize density by critical density to get overdensity
            df = df.copy()
            df[overdensity_col] = df["density"] / RHO_CRITICAL
            logger.info(f"Calculated overdensity using RHO_CRITICAL={RHO_CRITICAL}")
        else:
            raise ValueError(f"Column '{overdensity_col}' not found and 'density' column not available for calculation.")
    
    df = df.copy()
    # Bin: 0 if overdensity < threshold, 1 if >= threshold
    df['environment_bin'] = (df[overdensity_col] >= ENVIRONMENT_THRESHOLD).astype(int)
    logger.info(f"Environment binning applied with threshold {ENVIRONMENT_THRESHOLD} using RHO_CRITICAL={RHO_CRITICAL}")
    return df

def run_ks_tests(df: pd.DataFrame, metrics: List[str], bin_col: str = "environment_bin") -> List[Dict[str, Any]]:
    """
    Run two-sample Kolmogorov-Smirnov tests between low/high environmental bins.
    
    Args:
        df: DataFrame with metrics and bin column.
        metrics: List of metric column names to test.
        bin_col: Column name for environment bins.
    
    Returns:
        List of dicts containing test results.
    """
    results = []
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in dataframe, skipping.")
            continue
        
        low_group = df[df[bin_col] == 0][metric].dropna()
        high_group = df[df[bin_col] == 1][metric].dropna()
        
        if len(low_group) == 0 or len(high_group) == 0:
            logger.warning(f"Insufficient data in one bin for metric '{metric}', skipping KS test.")
            continue
        
        stat, pvalue = scipy_stats.ks_2samp(low_group, high_group)
        results.append({
            "metric": metric,
            "test": "ks_2samp",
            "statistic": float(stat),
            "p_value": float(pvalue),
            "n_low": len(low_group),
            "n_high": len(high_group)
        })
        logger.debug(f"KS test for {metric}: stat={stat:.4f}, p={pvalue:.4f}")
    
    return results

def apply_benjamini_hochberg(p_values: List[float], alpha: float = BH_THRESHOLD) -> List[bool]:
    """
    Apply Benjamini-Hochberg correction for multiple hypothesis testing.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        alpha: Significance level.
    
    Returns:
        List of booleans indicating whether to reject the null hypothesis.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # BH critical values
    critical_values = (np.arange(1, m + 1) / m) * alpha
    
    # Find the largest k such that p_(k) <= critical_k
    # Reject all hypotheses up to k
    reject = np.zeros(m, dtype=bool)
    for i in range(m - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            reject[:i+1] = True
            break
    
    # Map back to original order
    final_reject = np.zeros(m, dtype=bool)
    final_reject[sorted_indices] = reject
    return final_reject.tolist()

def run_spearman_correlations(df: pd.DataFrame, mass_col: str = "mass", metrics: List[str] = None) -> List[Dict[str, Any]]:
    """
    Compute Spearman's rho correlation between halo mass and each structural metric.
    
    Args:
        df: DataFrame with mass and metrics.
        mass_col: Name of the mass column.
        metrics: List of metric column names.
    
    Returns:
        List of dicts containing correlation results.
    """
    if metrics is None:
        metrics = ["shape", "spin", "concentration"]
    
    results = []
    for metric in metrics:
        if metric not in df.columns or mass_col not in df.columns:
            logger.warning(f"Missing columns for correlation: {metric} or {mass_col}")
            continue
        
        # Drop NaNs
        valid_data = df[[mass_col, metric]].dropna()
        if len(valid_data) < 3:
            logger.warning("Insufficient data for Spearman correlation.")
            continue
        
        rho, p_value = scipy_stats.spearmanr(valid_data[mass_col], valid_data[metric])
        results.append({
            "metric": metric,
            "correlation_type": "spearman",
            "rho": float(rho),
            "p_value": float(p_value),
            "n_samples": len(valid_data)
        })
        logger.debug(f"Spearman correlation {metric} vs mass: rho={rho:.4f}, p={p_value:.4f}")
    
    return results

def bullock_comparison(df: pd.DataFrame, mass_col: str = "mass", conc_col: str = "concentration") -> Dict[str, Any]:
    """
    Compare measured mass-concentration relation against Bullock et al. (2001) analytic fit.
    
    Args:
        df: DataFrame with mass and concentration.
        mass_col: Name of the mass column.
        conc_col: Name of the concentration column.
    
    Returns:
        Dict containing fit parameters, RMSE, and mean difference.
    """
    if conc_col not in df.columns or mass_col not in df.columns:
        return {"error": "Missing required columns"}
    
    # Bullock et al. (2001) fit: c(M) = c_200 * (M / M_200)^alpha
    # We need a pivot mass M_200. Often taken as 10^12 Msun/h or similar.
    # For this implementation, we assume M_200 is a characteristic mass, e.g., 1e12
    M_pivot = 1e12 
    
    c200 = BULLOCK_C200
    alpha = BULLOCK_ALPHA
    
    measured_mass = df[mass_col].values
    measured_conc = df[conc_col].values
    
    # Predicted concentration
    predicted_conc = c200 * (measured_mass / M_pivot) ** alpha
    
    # Calculate statistics
    rmse = np.sqrt(np.mean((measured_conc - predicted_conc) ** 2))
    mean_diff = np.mean(measured_conc - predicted_conc)
    
    logger.info(f"Bullock comparison: RMSE={rmse:.4f}, Mean Diff={mean_diff:.4f}")
    
    return {
        "model": "Bullock2001",
        "params": {"c_200": c200, "alpha": alpha, "M_pivot": M_pivot},
        "rmse": float(rmse),
        "mean_difference": float(mean_diff),
        "n_samples": len(measured_mass)
    }

def run_full_analysis_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    1. Load data
    2. Mass binning
    3. Environment binning (using RHO_CRITICAL)
    4. Run KS tests
    5. Apply BH correction
    6. Run Spearman correlations
    7. Bullock comparison
    8. Save results
    
    Args:
        input_path: Path to the processed parquet file.
        output_path: Path to save results JSON.
    
    Returns:
        Dictionary of all analysis results.
    """
    logger.info(f"Starting full analysis pipeline. Input: {input_path}, Output: {output_path}")
    
    # Load data
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} halos")
    
    # Binning
    df = mass_binning(df)
    df = environment_binning(df)
    
    # Metrics to test
    metrics = ["shape", "spin", "concentration"]
    
    # KS Tests
    ks_results = run_ks_tests(df, metrics)
    p_values = [r["p_value"] for r in ks_results]
    bh_rejections = apply_benjamini_hochberg(p_values)
    
    for i, res in enumerate(ks_results):
        res["rejected_bh"] = bh_rejections[i]
    
    # Spearman Correlations
    spearman_results = run_spearman_correlations(df)
    
    # Bullock Comparison
    bullock_results = bullock_comparison(df)
    
    # Compile results
    final_results = {
        "ks_tests": ks_results,
        "spearman_correlations": spearman_results,
        "bullock_comparison": bullock_results,
        "config": {
            "rho_critical": RHO_CRITICAL,
            "environment_threshold": ENVIRONMENT_THRESHOLD,
            "bullock_c200": BULLOCK_C200,
            "bullock_alpha": BULLOCK_ALPHA
        }
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return final_results