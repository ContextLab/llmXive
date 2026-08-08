import logging
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.config import RESULTS_DIR, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE

# Ensure logging is configured
logger = logging.getLogger(__name__)

def load_raw_evaluations() -> pd.DataFrame:
    """Load raw evaluations from CSV."""
    path = RESULTS_DIR / RAW_EVALUATIONS_FILE
    if not path.exists():
        raise FileNotFoundError(f"Raw evaluations file not found: {path}")
    return pd.read_csv(path)

def load_dataset_properties() -> pd.DataFrame:
    """Load dataset properties from JSON or CSV if available."""
    # Assuming properties are derived or stored elsewhere, for now returning a placeholder
    # In a real scenario, this would load from data/processed/properties.csv
    return pd.DataFrame()

def aggregate_log_variance(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate log variance metrics."""
    # Implementation placeholder for existing logic
    return raw_df.groupby(['dataset_id', 'model_name']).agg({
        'accuracy': ['mean', 'std'],
        'f1_score': ['mean', 'std']
    }).reset_index()

def compute_regression_residuals(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    """Compute residuals from log-log regression."""
    # Implementation placeholder
    return aggregated_df

def run_permutation_test(accuracy_scores: Dict[str, List[float]], n_permutations: int = 1000) -> Tuple[float, float]:
    """
    Run permutation test for two groups of scores.
    Returns (statistic, p_value).
    """
    # Implementation placeholder for existing logic
    return 0.0, 1.0

def run_full_analysis(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Run full analysis pipeline."""
    # Placeholder for existing logic
    return raw_df

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg procedure to control False Discovery Rate (FDR).
    
    Parameters:
    -----------
    p_values : List[float]
        List of raw p-values from hypothesis tests.
    alpha : float
        Desired FDR level (default 0.05).
    
    Returns:
    --------
    Tuple[List[float], List[bool]]
        - Adjusted p-values (q-values)
        - Boolean list indicating significance (True if adj_p < alpha)
    
    Notes:
    ------
    This implements the Benjamini-Hochberg step-up procedure.
    It controls the FDR, not the FWER (Family-Wise Error Rate).
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    # rank i goes from 1 to n
    ranks = np.arange(1, n + 1)
    bh_thresholds = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= (k/n) * alpha
    # Then reject all hypotheses with p <= p_(k)
    # For adjusted p-values, we use the monotonicity constraint
    
    # Calculate adjusted p-values (q-values)
    # q_(i) = min( (n/i) * p_(i), q_(i+1) ) working backwards
    adjusted_p_values = np.zeros(n)
    adjusted_p_values[-1] = min(1.0, sorted_p_values[-1] * (n / n))
    
    for i in range(n - 2, -1, -1):
        # Calculate raw adjusted p-value for this rank
        raw_adj = min(1.0, sorted_p_values[i] * (n / (i + 1)))
        # Enforce monotonicity: q_(i) <= q_(i+1)
        adjusted_p_values[i] = min(raw_adj, adjusted_p_values[i + 1])
    
    # Map adjusted p-values back to original order
    final_adjusted_p_values = np.zeros(n)
    final_adjusted_p_values[sorted_indices] = adjusted_p_values
    
    # Determine significance
    significant = final_adjusted_p_values < alpha
    
    return final_adjusted_p_values.tolist(), significant.tolist()

def apply_global_bh_correction():
    """
    Apply Benjamini-Hochberg correction globally across ALL hypothesis tests:
    1. Correlation tests (from results/correlation_results.csv)
    2. Permutation tests (from results/permutation_results.csv)
    
    This satisfies FR-007 requirement for multiple comparison correction.
    """
    logger.info("Applying global Benjamini-Hochberg correction to all hypothesis tests...")
    
    # Load correlation results
    correlation_path = RESULTS_DIR / CORRELATION_RESULTS_FILE
    if not correlation_path.exists():
        logger.warning(f"Correlation results file not found: {correlation_path}. Skipping correlation correction.")
        correlation_df = pd.DataFrame()
    else:
        correlation_df = pd.read_csv(correlation_path)
    
    # Load permutation results
    permutation_path = RESULTS_DIR / PERMUTATION_RESULTS_FILE
    if not permutation_path.exists():
        logger.warning(f"Permutation results file not found: {permutation_path}. Skipping permutation correction.")
        permutation_df = pd.DataFrame()
    else:
        permutation_df = pd.read_csv(permutation_path)
    
    all_p_values = []
    all_sources = []  # Track source of each p-value
    all_rows = []     # Track original row data for reconstruction
    
    # Collect p-values from correlation results
    # The correlation results have pearson_p_value and spearman_p_value
    # We treat each as a separate hypothesis test
    if not correlation_df.empty:
        for idx, row in correlation_df.iterrows():
            # Add Pearson p-value
            if pd.notna(row.get('pearson_p_value')):
                all_p_values.append(row['pearson_p_value'])
                all_sources.append(('correlation', 'pearson', idx))
                all_rows.append(('correlation', 'pearson', row.to_dict()))
            
            # Add Spearman p-value
            if pd.notna(row.get('spearman_p_value')):
                all_p_values.append(row['spearman_p_value'])
                all_sources.append(('correlation', 'spearman', idx))
                all_rows.append(('correlation', 'spearman', row.to_dict()))
    
    # Collect p-values from permutation results
    if not permutation_df.empty:
        for idx, row in permutation_df.iterrows():
            if pd.notna(row.get('raw_p_value')):
                all_p_values.append(row['raw_p_value'])
                all_sources.append(('permutation', 'raw', idx))
                all_rows.append(('permutation', 'raw', row.to_dict()))
    
    if not all_p_values:
        logger.warning("No p-values found to correct. Skipping BH correction.")
        return
    
    logger.info(f"Applying BH correction to {len(all_p_values)} hypothesis tests.")
    
    # Apply Benjamini-Hochberg
    adjusted_p_values, significant = apply_benjamini_hochberg(all_p_values, alpha=0.05)
    
    # Update correlation results
    if not correlation_df.empty:
        # Create a mapping from (source_type, p_type, idx) to adjusted p-value
        adj_map = {}
        for i, (source, p_type, idx) in enumerate(all_sources):
            if source == 'correlation':
                adj_map[(p_type, idx)] = adjusted_p_values[i]
        
        # Update correlation_df with adjusted p-values
        for idx in correlation_df.index:
            if ('pearson', idx) in adj_map:
                correlation_df.loc[idx, 'adj_pearson_p_value'] = adj_map[('pearson', idx)]
                correlation_df.loc[idx, 'pearson_significant'] = significant[all_sources.index(('correlation', 'pearson', idx))]
            if ('spearman', idx) in adj_map:
                correlation_df.loc[idx, 'adj_spearman_p_value'] = adj_map[('spearman', idx)]
                correlation_df.loc[idx, 'spearman_significant'] = significant[all_sources.index(('correlation', 'spearman', idx))]
        
        # Save updated correlation results
        correlation_df.to_csv(correlation_path, index=False)
        logger.info(f"Updated correlation results with BH correction: {correlation_path}")
    
    # Update permutation results
    if not permutation_df.empty:
        # Create a mapping from (source_type, idx) to adjusted p-value
        adj_map = {}
        for i, (source, p_type, idx) in enumerate(all_sources):
            if source == 'permutation':
                adj_map[idx] = adjusted_p_values[i]
        
        # Update permutation_df with adjusted p-values
        for idx in permutation_df.index:
            if idx in adj_map:
                permutation_df.loc[idx, 'adj_p_value'] = adj_map[idx]
                permutation_df.loc[idx, 'significant'] = significant[all_sources.index(('permutation', 'raw', idx))]
        
        # Save updated permutation results
        permutation_df.to_csv(permutation_path, index=False)
        logger.info(f"Updated permutation results with BH correction: {permutation_path}")
    
    logger.info("Global Benjamini-Hochberg correction completed successfully.")
    return