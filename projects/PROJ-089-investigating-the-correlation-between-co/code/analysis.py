"""
Analysis Module: Correlation, Meta-analysis, and Sensitivity Analysis.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import (
    DATA_PROCESSED,
    DATA_RESULTS,
    UNIFIED_METRICS_FILE,
    CORRELATION_RESULTS_FILE,
    SENSITIVITY_ANALYSIS_FILE,
    META_ANALYSIS_RESULTS_FILE,
    VIF_THRESHOLD,
    ensure_directories,
    get_config_summary
)
from utils import get_logger

logger = get_logger(__name__)

def load_unified_metrics() -> pd.DataFrame:
    """Loads the unified metrics CSV."""
    # The config now has a 'paths' key in get_config_summary, but we need the path directly.
    # We use the constant UNIFIED_METRICS_FILE defined in config.
    if not UNIFIED_METRICS_FILE.exists():
        raise FileNotFoundError(f"Unified metrics file not found: {UNIFIED_METRICS_FILE}")
    return pd.read_csv(UNIFIED_METRICS_FILE)

def run_vif_check(df: pd.DataFrame) -> pd.DataFrame:
    """
    Checks Variance Inflation Factor for covariates.
    T018
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Select numeric covariates
    cols = ['avg_loc', 'contributor_count']
    # Filter to existing columns
    available_cols = [c for c in cols if c in df.columns]
    
    if len(available_cols) < 2:
        logger.warning("Not enough covariates for VIF check.")
        return pd.DataFrame(columns=["covariate_name", "vif_value", "status"])
    
    X = df[available_cols].dropna()
    if X.empty:
        return pd.DataFrame(columns=["covariate_name", "vif_value", "status"])
    
    # Add constant
    X_const = sm.add_constant(X)
    
    vif_results = []
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            status = "OK" if vif < VIF_THRESHOLD else "HIGH"
            vif_results.append({
                "covariate_name": col,
                "vif_value": vif,
                "status": status
            })
        except Exception as e:
            logger.warning(f"VIF calculation failed for {col}: {e}")
    
    vif_df = pd.DataFrame(vif_results)
    vif_df.to_csv(DATA_RESULTS / "vif_report.csv", index=False)
    return vif_df

def run_correlation_analysis(dataframe: pd.DataFrame, thresholds: List[int] = [5, 10, 20]) -> Dict[int, Dict[str, float]]:
    """
    Runs correlation analysis for different thresholds.
    T015b, T022
    """
    results = {}
    for threshold in thresholds:
        # Filter
        filtered_df = dataframe[dataframe['avg_loc'] >= threshold]
        if filtered_df.empty:
            results[threshold] = {'r': 0.0, 'p': 1.0, 'n': 0}
            continue
        
        # Correlation
        # Pearson
        corr, p = filtered_df['total_lines_changed'].corr(filtered_df['debt_score'], method='pearson'), 0.0
        # Calculate p-value manually or use scipy
        from scipy.stats import pearsonr
        try:
            corr, p = pearsonr(filtered_df['total_lines_changed'], filtered_df['debt_score'])
        except Exception as e:
            logger.warning(f"Correlation failed for threshold {threshold}: {e}")
            corr, p = 0.0, 1.0
        
        results[threshold] = {'r': float(corr), 'p': float(p), 'n': len(filtered_df)}
    return results

def run_meta_analysis() -> pd.DataFrame:
    """
    Performs Fisher-transformed meta-analysis.
    T021
    """
    # Load per-repo correlations (T020 output)
    # Assuming per_repo_correlations.csv exists or we compute from unified_metrics
    # For this task, we assume we compute from unified_metrics grouped by repo_id
    df = load_unified_metrics()
    
    per_repo = []
    for repo_id, group in df.groupby('repo_id'):
        if len(group) < 2:
            continue
        try:
            from scipy.stats import pearsonr
            r, p = pearsonr(group['total_lines_changed'], group['debt_score'])
            per_repo.append({'repo_id': repo_id, 'r': r, 'n': len(group)})
        except Exception:
            continue
    
    if not per_repo:
        logger.warning("No per-repo correlations found for meta-analysis.")
        return pd.DataFrame()
    
    per_repo_df = pd.DataFrame(per_repo)
    
    # Fisher Z
    # Handle r=1 or r=-1
    per_repo_df['r'] = per_repo_df['r'].clip(-0.999, 0.999)
    per_repo_df['z'] = 0.5 * np.log((1 + per_repo_df['r']) / (1 - per_repo_df['r']))
    per_repo_df['se'] = 1 / np.sqrt(per_repo_df['n'] - 3)
    
    # Inverse-variance weighted
    weights = 1 / (per_repo_df['se'] ** 2)
    z_combined = np.sum(per_repo_df['z'] * weights) / np.sum(weights)
    se_combined = np.sqrt(1 / np.sum(weights))
    
    # Back to r
    r_combined = (np.exp(2 * z_combined) - 1) / (np.exp(2 * z_combined) + 1)
    
    # P-value for z_combined
    # Z-score test
    z_stat = z_combined / se_combined
    from scipy.stats import norm
    p_value = 2 * (1 - norm.cdf(abs(z_stat)))
    
    result = pd.DataFrame([{
        'method': 'Fisher_Z_Meta_Analysis',
        'combined_r': r_combined,
        'combined_se': se_combined,
        'p_value': p_value,
        'k_studies': len(per_repo_df)
    }])
    
    result.to_csv(META_ANALYSIS_RESULTS_FILE, index=False)
    return result

def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Runs sensitivity analysis with fixed thresholds [5, 10, 20].
    T022
    """
    df = load_unified_metrics()
    thresholds = [5, 10, 20]
    
    results = []
    for t in thresholds:
        filtered = df[df['avg_loc'] >= t]
        if len(filtered) < 2:
            results.append({'threshold': t, 'r_value': 0.0, 'p_value': 1.0, 'n': 0})
            continue
        
        from scipy.stats import pearsonr
        try:
            r, p = pearsonr(filtered['total_lines_changed'], filtered['debt_score'])
        except Exception:
            r, p = 0.0, 1.0
        
        results.append({'threshold': t, 'r_value': r, 'p_value': p, 'n': len(filtered)})
    
    res_df = pd.DataFrame(results)
    res_df.to_csv(SENSITIVITY_ANALYSIS_FILE, index=False)
    return res_df

def run_analysis() -> Dict[str, Any]:
    """Runs the full analysis pipeline."""
    ensure_directories()
    logger.info("Starting Analysis Pipeline")
    
    try:
        # VIF
        # vif_df = run_vif_check(load_unified_metrics()) # Optional if data exists
        
        # Sensitivity
        sens_df = run_sensitivity_analysis()
        
        # Meta
        meta_df = run_meta_analysis()
        
        return {
            'sensitivity': sens_df,
            'meta': meta_df
        }
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        raise

def main():
    """Entry point."""
    logger.info("Running analysis.py main")
    try:
        run_analysis()
        logger.info("Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()