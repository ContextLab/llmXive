import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

from utils.config import get_config

logger = logging.getLogger(__name__)

def load_metrics_and_drf() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load subject metrics and Dream Recall Frequency (DRF) values.
    
    Returns:
        Tuple of (metrics_df, drf_series)
    """
    config = get_config()
    metrics_path = Path(config['data_dir']) / 'metrics' / 'subject_metrics.csv'
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. "
                                "Run metric extraction (US2) before statistical analysis.")
    
    df = pd.read_csv(metrics_path)
    
    # Ensure DRF column exists
    if 'dream_recall_frequency' not in df.columns:
        raise ValueError("Column 'dream_recall_frequency' not found in metrics CSV. "
                         "Check data pipeline (US1) for metadata validation.")
    
    drf = df['dream_recall_frequency']
    
    logger.info(f"Loaded {len(df)} subjects with DRF data")
    return df, drf

def calculate_spearman_correlations(metrics_df: pd.DataFrame, drf: pd.Series) -> Dict[str, Dict[str, float]]:
    """
    Calculate Spearman correlation between each metric and DRF.
    
    Args:
        metrics_df: DataFrame containing network metrics
        drf: Series containing Dream Recall Frequency values
        
    Returns:
        Dictionary mapping metric name to {rho, p_value}
    """
    results = {}
    
    # Identify numeric metric columns (exclude subject_id, dream_recall_frequency)
    exclude_cols = ['subject_id', 'dream_recall_frequency']
    metric_cols = [col for col in metrics_df.columns 
                  if col not in exclude_cols and pd.api.types.is_numeric_dtype(metrics_df[col])]
    
    logger.info(f"Calculating correlations for {len(metric_cols)} metrics")
    
    for col in metric_cols:
        # Drop rows with NaN in either column
        valid_mask = metrics_df[col].notna() & drf.notna()
        x = metrics_df.loc[valid_mask, col]
        y = drf.loc[valid_mask]
        
        if len(x) < 3:
            logger.warning(f"Insufficient data points for {col}, skipping")
            continue
        
        rho, p_val = spearmanr(x, y)
        results[col] = {
            'rho': float(rho),
            'p_uncorrected': float(p_val)
        }
        logger.debug(f"{col}: rho={rho:.4f}, p={p_val:.4f}")
    
    return results

def apply_fdr_correction(correlation_results: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values using Benjamini-Hochberg.
    
    Args:
        correlation_results: Dictionary from calculate_spearman_correlations
        
    Returns:
        Updated dictionary with 'p_fdr_corrected' added to each metric
    """
    if not correlation_results:
        logger.warning("No correlations to correct")
        return correlation_results
    
    # Extract p-values and metric names
    p_values = [v['p_uncorrected'] for v in correlation_results.values()]
    metric_names = list(correlation_results.keys())
    
    if len(p_values) == 0:
        return correlation_results
    
    # Apply FDR correction using Benjamini-Hochberg method
    # reject: boolean array indicating which hypotheses are rejected
    # pvals_corrected: adjusted p-values
    reject, pvals_corrected, _, _ = multipletests(
        p_values, 
        alpha=0.05, 
        method='fdr_bh'
    )
    
    # Update results with corrected p-values
    for i, metric in enumerate(metric_names):
        correlation_results[metric]['p_fdr_corrected'] = float(pvals_corrected[i])
        correlation_results[metric]['fdr_rejected'] = bool(reject[i])
        logger.info(f"{metric}: p_uncorrected={p_values[i]:.4f}, p_fdr={pvals_corrected[i]:.4f}, significant={reject[i]}")
    
    return correlation_results

def run_correlation_analysis(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Full correlation analysis pipeline: load data, calculate correlations, apply FDR.
    
    Args:
        output_path: Optional path to save results JSON. If None, uses config default.
        
    Returns:
        Dictionary containing analysis results
    """
    config = get_config()
    if output_path is None:
        output_path = str(Path(config['results_dir']) / 'stats.json')
    
    # Load data
    metrics_df, drf = load_metrics_and_drf()
    
    # Calculate correlations
    corr_results = calculate_spearman_correlations(metrics_df, drf)
    
    # Apply FDR correction
    corr_results = apply_fdr_correction(corr_results)
    
    # Prepare output
    output = {
        'n_subjects': int(len(drf)),
        'n_metrics_tested': len(corr_results),
        'correlations': corr_results
    }
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return output

def main():
    """Entry point for statistical analysis with FDR correction."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_correlation_analysis()
        print(json.dumps(results, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())