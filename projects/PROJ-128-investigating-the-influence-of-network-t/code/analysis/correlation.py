"""
Statistical correlation analysis between structural and dynamic brain network metrics.

This module implements:
1. Normality testing (Shapiro-Wilk) to select Pearson vs. Spearman correlation.
2. Correlation calculation across the cohort.
3. Benjamini-Hochberg FDR correction on p-values.
4. End-to-end analysis pipeline.
"""
import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings
import os

# Suppress specific warnings if needed, but allow critical errors
warnings.filterwarnings('ignore', category=RuntimeWarning)

def check_normality(data_series: pd.Series, alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk normality test on a data series.
    
    Args:
        data_series: Pandas Series of numeric values.
        alpha: Significance level for the test (default 0.05).
    
    Returns:
        Tuple of (is_normal, p_value).
        is_normal is True if p-value > alpha (fail to reject null hypothesis).
    """
    if len(data_series.dropna()) < 3:
        # Not enough data for normality test; assume normal to proceed or handle as edge case
        # For small N, statistical power is low, but we proceed with Pearson as default
        return True, 1.0
    
    clean_data = data_series.dropna().values
    if len(clean_data) < 3:
        return True, 1.0

    try:
        stat, p_val = shapiro(clean_data)
        return p_val > alpha, p_val
    except Exception:
        # If test fails (e.g., constant data), assume normal to avoid crash, 
        # though constant data will result in NaN correlation later.
        return True, 1.0

def calculate_correlation(
    x: pd.Series, 
    y: pd.Series, 
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value between two series.
    
    Args:
        x: First data series.
        y: Second data series.
        method: 'pearson' or 'spearman'.
    
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    # Drop NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return np.nan, np.nan
    
    if method == 'pearson':
        r, p = pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        r, p = spearmanr(x_clean, y_clean)
    else:
        raise ValueError(f"Unknown correlation method: {method}")
    
    return r, p

def benjamini_hochberg_fdr(
    p_values: List[float], 
    alpha: float = 0.05
) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: FDR significance level (default 0.05).
    
    Returns:
        Tuple of (significant_flags, adjusted_p_values).
        significant_flags is a list of booleans indicating if the null is rejected.
    """
    if not p_values:
        return [], []
    
    # Filter out NaNs for calculation but track indices
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    if not valid_indices:
        return [False] * len(p_values), [np.nan] * len(p_values)
    
    raw_p_vals = [p_values[i] for i in valid_indices]
    n = len(raw_p_vals)
    
    # Sort p-values
    sorted_indices = np.argsort(raw_p_vals)
    sorted_p_vals = np.array([raw_p_vals[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted_p_vals = np.zeros(n)
    for i in range(n):
        # BH formula: p_i * (n / rank)
        # rank is i+1 (1-based)
        rank = i + 1
        adjusted = sorted_p_vals[i] * (n / rank)
        # Ensure monotonicity (cumulative max from the end)
        adjusted_p_vals[i] = adjusted
    
    # Enforce monotonicity: adjusted p-value at i must be <= adjusted p-value at i+1
    # We iterate backwards
    for i in range(n - 2, -1, -1):
        if adjusted_p_vals[i] > adjusted_p_vals[i + 1]:
            adjusted_p_vals[i] = adjusted_p_vals[i + 1]
    
    # Cap at 1.0
    adjusted_p_vals = np.minimum(adjusted_p_vals, 1.0)
    
    # Map back to original order
    final_adjusted = [np.nan] * len(p_values)
    final_flags = [False] * len(p_values)
    
    for idx, adj_val in zip(valid_indices, adjusted_p_vals):
        final_adjusted[idx] = adj_val
        final_flags[idx] = adj_val <= alpha
    
    return final_flags, final_adjusted

def run_correlation_analysis(
    structural_df: pd.DataFrame,
    dynamic_df: pd.DataFrame,
    structural_cols: List[str],
    dynamic_cols: List[str],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Perform correlation analysis between structural and dynamic metrics.
    
    Args:
        structural_df: DataFrame with structural metrics (index: subject_id).
        dynamic_df: DataFrame with dynamic metrics (index: subject_id).
        structural_cols: List of column names in structural_df to test.
        dynamic_cols: List of column names in dynamic_df to test.
        alpha: Significance level for normality test and FDR.
    
    Returns:
        DataFrame with columns: 
            struct_metric, dynamic_metric, correlation_method, r_value, p_value, is_significant_fdr
    """
    # Merge on subject_id (assuming both have 'subject_id' or are indexed by it)
    # Ensure we are aligning on the subject ID
    if 'subject_id' in structural_df.columns:
        structural_df = structural_df.set_index('subject_id')
    if 'subject_id' in dynamic_df.columns:
        dynamic_df = dynamic_df.set_index('subject_id')
    
    # Inner join to keep only subjects with both metrics
    merged_df = structural_df.join(dynamic_df, how='inner')
    
    if merged_df.empty:
        return pd.DataFrame(columns=['struct_metric', 'dynamic_metric', 'correlation_method', 'r_value', 'p_value', 'is_significant_fdr'])
    
    results = []
    all_p_values = []
    
    # Determine correlation method for each structural metric
    # We test normality on the structural metrics. Dynamic metrics are assumed to be tested similarly 
    # or we can default to Spearman if either is non-normal. 
    # Strategy: Test normality for each structural column. If non-normal, use Spearman for all pairs with that column.
    # Or simpler: Test normality for the merged pairs.
    
    # Let's test normality for each structural metric across the cohort
    structural_methods = {}
    for col in structural_cols:
        if col in merged_df.columns:
            is_normal, _ = check_normality(merged_df[col], alpha=alpha)
            # If normal, use Pearson, else Spearman
            structural_methods[col] = 'pearson' if is_normal else 'spearman'
        else:
            structural_methods[col] = 'spearman' # Default to robust if missing
    
    # Test dynamic metrics too? Usually we test the pair.
    # For simplicity, if structural is non-normal, use Spearman. 
    # If structural is normal, we check dynamic. If dynamic is non-normal, use Spearman.
    dynamic_methods = {}
    for col in dynamic_cols:
        if col in merged_df.columns:
            is_normal, _ = check_normality(merged_df[col], alpha=alpha)
            dynamic_methods[col] = 'pearson' if is_normal else 'spearman'
        else:
            dynamic_methods[col] = 'spearman'

    for s_col in structural_cols:
        if s_col not in merged_df.columns:
            continue
        
        # Determine method for this structural metric
        # If either s_col or d_col is non-normal, use Spearman
        method_s = structural_methods.get(s_col, 'spearman')
        
        for d_col in dynamic_cols:
            if d_col not in merged_df.columns:
                continue
            
            method_d = dynamic_methods.get(d_col, 'spearman')
            method = 'pearson' if (method_s == 'pearson' and method_d == 'pearson') else 'spearman'
            
            s_series = merged_df[s_col]
            d_series = merged_df[d_col]
            
            r, p = calculate_correlation(s_series, d_series, method=method)
            
            results.append({
                'struct_metric': s_col,
                'dynamic_metric': d_col,
                'correlation_method': method,
                'r_value': r,
                'p_value': p
            })
            all_p_values.append(p)
    
    if not results:
        return pd.DataFrame(columns=['struct_metric', 'dynamic_metric', 'correlation_method', 'r_value', 'p_value', 'is_significant_fdr'])
    
    results_df = pd.DataFrame(results)
    
    # Apply FDR correction
    if len(all_p_values) > 0:
        # Handle NaNs in p-values for FDR calculation
        # Replace NaN with 1.0 for calculation, then restore
        p_vals_for_fdr = [1.0 if np.isnan(p) else p for p in all_p_values]
        sig_flags, adj_p_vals = benjamini_hochberg_fdr(p_vals_for_fdr, alpha=alpha)
        
        # Restore NaNs where original was NaN
        final_sig_flags = []
        final_adj_p_vals = []
        for orig_p, flag, adj_p in zip(all_p_values, sig_flags, adj_p_vals):
            if np.isnan(orig_p):
                final_sig_flags.append(False)
                final_adj_p_vals.append(np.nan)
            else:
                final_sig_flags.append(flag)
                final_adj_p_vals.append(adj_p)
        
        results_df['p_value_fdr'] = final_adj_p_vals
        results_df['is_significant_fdr'] = final_sig_flags
    else:
        results_df['p_value_fdr'] = np.nan
        results_df['is_significant_fdr'] = False
    
    # Reorder columns
    results_df = results_df[['struct_metric', 'dynamic_metric', 'correlation_method', 'r_value', 'p_value', 'p_value_fdr', 'is_significant_fdr']]
    
    return results_df

def main():
    """
    Main entry point for correlation analysis.
    Loads data from data/processed/, runs analysis, saves to data/processed/correlation_results.csv.
    """
    print("Starting correlation analysis...")
    
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data' / 'processed'
    
    structural_path = data_dir / 'structural_metrics.csv'
    dynamic_path = data_dir / 'dynamic_metrics.csv'
    output_path = data_dir / 'correlation_results.csv'
    
    if not structural_path.exists():
        raise FileNotFoundError(f"Structural metrics file not found: {structural_path}")
    if not dynamic_path.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_path}")
    
    # Load data
    structural_df = pd.read_csv(structural_path)
    dynamic_df = pd.read_csv(dynamic_path)
    
    # Define metrics to correlate
    # Structural metrics typically: global_efficiency, avg_clustering, modularity
    structural_cols = [col for col in structural_df.columns if col not in ['subject_id', 'density']]
    # Dynamic metrics: mean_dwell_time, num_visits (per state, but we might aggregate or iterate states)
    # Assuming dynamic_df has subject_id, state_id, mean_dwell_time, num_visits
    # We need to pivot or iterate states. For now, assume we correlate structural with mean_dwell_time aggregated or per state.
    # If dynamic_df is long (one row per subject per state), we might need to pivot.
    # Let's assume the task requires correlating structural metrics with dynamic metrics.
    # If dynamic_df has multiple rows per subject (one per state), we should pivot to wide or aggregate.
    # For this skeleton, we assume dynamic_df is already aggregated or we select specific columns.
    # If dynamic_df is long, we pivot: index=subject_id, columns=state_id, values=mean_dwell_time
    
    if 'state_id' in dynamic_df.columns:
        # Pivot to wide format: one row per subject, columns for each state's dwell time
        dynamic_wide = dynamic_df.pivot(index='subject_id', columns='state_id', values='mean_dwell_time')
        dynamic_wide.columns = [f'dwell_time_state_{c}' for c in dynamic_wide.columns]
        dynamic_wide = dynamic_wide.reset_index()
        dynamic_cols = [c for c in dynamic_wide.columns if c != 'subject_id']
        dynamic_df = dynamic_wide
    else:
        dynamic_cols = [col for col in dynamic_df.columns if col not in ['subject_id', 'state_id']]
    
    print(f"Structural columns: {structural_cols}")
    print(f"Dynamic columns: {dynamic_cols}")
    
    # Run analysis
    results = run_correlation_analysis(
        structural_df,
        dynamic_df,
        structural_cols,
        dynamic_cols,
        alpha=0.05
    )
    
    # Save results
    results.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    print(f"Total correlations: {len(results)}")
    print(f"Significant findings (FDR < 0.05): {results['is_significant_fdr'].sum()}")

if __name__ == '__main__':
    main()
