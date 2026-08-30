import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings
import os

def check_normality(data: pd.Series, alpha: float = 0.05) -> Tuple[bool, float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Series of values to test.
        alpha: Significance level.
        
    Returns:
        Tuple of (is_normal, statistic, p_value).
    """
    if len(data) < 3:
        warnings.warn("Sample size too small for Shapiro-Wilk test. Assuming normal.")
        return True, 0.0, 1.0
    
    try:
        stat, p_val = shapiro(data)
        is_normal = p_val > alpha
        return is_normal, stat, p_val
    except Exception as e:
        warnings.warn(f"Shapiro-Wilk test failed: {e}. Assuming normal.")
        return True, 0.0, 1.0

def calculate_correlation(x: pd.Series, y: pd.Series, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value.
    
    Args:
        x: First variable.
        y: Second variable.
        method: 'pearson' or 'spearman'.
        
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    # Drop NaN pairs
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan
    
    if method == 'pearson':
        r, p = pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        r, p = spearmanr(x_clean, y_clean)
    else:
        raise ValueError(f"Unknown correlation method: {method}")
        
    return r, p

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of raw p-values.
        alpha: FDR significance level.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags).
    """
    n = len(p_values)
    if n == 0:
        return [], []
        
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        # BH formula: p_adj = p * n / rank
        adjusted_p[i] = sorted_p[i] * n / rank
        
    # Ensure monotonicity (cumulative min from largest to smallest)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
        
    # Clip to [0, 1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    # Reorder to original indices
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted_p
    
    # Determine significance
    significant = final_adjusted < alpha
    
    return final_adjusted.tolist(), significant.tolist()

def run_correlation_analysis(structural_df: pd.DataFrame, dynamic_df: pd.DataFrame, 
                             alpha_normality: float = 0.05, alpha_fdr: float = 0.05) -> pd.DataFrame:
    """
    Run full correlation analysis between structural and dynamic metrics.
    
    Args:
        structural_df: DataFrame with structural metrics (index: subject_id).
        dynamic_df: DataFrame with dynamic metrics (index: subject_id).
        alpha_normality: Alpha for normality test.
        alpha_fdr: Alpha for FDR correction.
        
    Returns:
        DataFrame with correlation results (r, p, fdr_p, significant).
    """
    # Merge on subject_id
    merged = structural_df.merge(dynamic_df, left_index=True, right_index=True, suffixes=('_struct', '_dyn'))
    
    # Identify metric columns
    struct_cols = [c for c in merged.columns if c.endswith('_struct')]
    dyn_cols = [c for c in merged.columns if c.endswith('_dyn')]
    
    results = []
    
    for s_col in struct_cols:
        for d_col in dyn_cols:
            s_name = s_col.replace('_struct', '')
            d_name = d_col.replace('_dyn', '')
            
            x = merged[s_col]
            y = merged[d_col]
            
            # Check normality
            is_normal_s, _, _ = check_normality(x, alpha_normality)
            is_normal_d, _, _ = check_normality(y, alpha_normality)
            
            method = 'pearson' if (is_normal_s and is_normal_d) else 'spearman'
            
            r, p = calculate_correlation(x, y, method)
            
            results.append({
                'structural_metric': s_name,
                'dynamic_metric': d_name,
                'method': method,
                'r': r,
                'p_raw': p
            })
    
    results_df = pd.DataFrame(results)
    
    if results_df.empty:
        return results_df
    
    # Apply FDR correction
    p_values = results_df['p_raw'].tolist()
    adj_p, sig_flags = benjamini_hochberg_fdr(p_values, alpha_fdr)
    
    results_df['p_fdr'] = adj_p
    results_df['significant'] = sig_flags
    
    return results_df

def main():
    """
    Main entry point for correlation analysis.
    Loads data, runs analysis, and saves results.
    """
    from config import get_config_dict
    config = get_config_dict()
    
    # Load data
    structural_path = config['paths']['processed_structural_metrics']
    dynamic_path = config['paths']['processed_dynamic_metrics']
    
    if not os.path.exists(structural_path) or not os.path.exists(dynamic_path):
        raise FileNotFoundError("Processed metric files not found. Run main.py first.")
        
    structural_df = pd.read_csv(structural_path, index_col=0)
    dynamic_df = pd.read_csv(dynamic_path, index_col=0)
    
    # Run analysis
    results = run_correlation_analysis(structural_df, dynamic_df)
    
    # Save results
    output_path = config['paths']['correlation_results']
    results.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    
    # Edge case handling: Zero significant findings
    if results['significant'].sum() == 0:
        print("WARNING: FDR correction yielded zero significant findings.")
        print("This is explicitly noted in the report as per T028.")
        
    return results

if __name__ == "__main__":
    main()