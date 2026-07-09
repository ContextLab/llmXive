import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings
import os

# Import config for paths
from config import get_config_dict, ensure_directories

def check_normality(data: pd.Series, alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: The data series to test.
        alpha: Significance level.
        
    Returns:
        Tuple of (is_normal, p_value).
    """
    if len(data) < 3:
        warnings.warn("Sample size too small for Shapiro-Wilk test. Assuming normality.")
        return True, 1.0
        
    stat, p_val = shapiro(data)
    return p_val > alpha, p_val

def calculate_correlation(x: pd.Series, y: pd.Series, method: str = 'pearson') -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value.
    
    Args:
        x: First variable.
        y: Second variable.
        method: 'pearson' or 'spearman'.
        
    Returns:
        Tuple of (correlation, p_value).
    """
    if method == 'pearson':
        corr, p_val = pearsonr(x, y)
    elif method == 'spearman':
        corr, p_val = spearmanr(x, y)
    else:
        raise ValueError(f"Unknown correlation method: {method}")
    return corr, p_val

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of raw p-values.
        alpha: FDR threshold.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags).
    """
    n = len(p_values)
    if n == 0:
        return [], []
        
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted_pvals = np.zeros(n)
    for i in range(n):
        # BH formula: p * n / rank
        rank = i + 1
        adjusted_pvals[i] = sorted_pvals[i] * n / rank
        
    # Ensure monotonicity (cumulative min from largest to smallest)
    for i in range(n - 2, -1, -1):
        adjusted_pvals[i] = min(adjusted_pvals[i], adjusted_pvals[i+1])
        
    # Ensure values are within [0, 1]
    adjusted_pvals = np.clip(adjusted_pvals, 0, 1)
    
    # Determine significance
    significant = adjusted_pvals < alpha
    
    # Restore original order
    final_adjusted = np.zeros(n)
    final_significant = np.zeros(n, dtype=bool)
    for i, idx in enumerate(sorted_indices):
        final_adjusted[idx] = adjusted_pvals[i]
        final_significant[idx] = significant[i]
        
    return final_adjusted.tolist(), final_significant.tolist()

def run_correlation_analysis(structural_df: pd.DataFrame, dynamic_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run correlation analysis between structural and dynamic metrics.
    
    Args:
        structural_df: DataFrame with structural metrics (must have 'subject_id' and metric columns).
        dynamic_df: DataFrame with dynamic metrics (must have 'subject_id' and metric columns).
        
    Returns:
        DataFrame with correlation results (r, p, fdr_p, significant).
    """
    # Merge on subject_id
    merged = pd.merge(structural_df, dynamic_df, on='subject_id', how='inner')
    
    if merged.empty:
        raise ValueError("No subjects found after merging structural and dynamic data.")
        
    # Identify metric columns (exclude subject_id)
    struct_cols = [c for c in structural_df.columns if c != 'subject_id']
    dynamic_cols = [c for c in dynamic_df.columns if c != 'subject_id']
    
    results = []
    
    for s_col in struct_cols:
        for d_col in dynamic_cols:
            x = merged[s_col]
            y = merged[d_col]
            
            # Check normality
            is_normal, _ = check_normality(x)
            is_normal_y, _ = check_normality(y)
            
            # Choose method based on normality
            method = 'pearson' if (is_normal and is_normal_y) else 'spearman'
            
            # Calculate correlation
            r, p_val = calculate_correlation(x, y, method)
            
            results.append({
                'structural_metric': s_col,
                'dynamic_metric': d_col,
                'correlation_method': method,
                'r_value': r,
                'p_value': p_val
            })
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    if results_df.empty:
        return results_df
        
    # Apply FDR correction
    p_values = results_df['p_value'].tolist()
    adj_p, sig_flags = benjamini_hochberg_fdr(p_values, alpha=0.05)
    
    results_df['fdr_p_value'] = adj_p
    results_df['significant'] = sig_flags
    
    return results_df

def main():
    """
    Main entry point to generate correlation results CSV.
    """
    config = get_config_dict()
    ensure_directories()
    
    # Load processed data
    struct_path = config['paths']['processed_structural_metrics']
    dyn_path = config['paths']['processed_dynamic_metrics']
    
    if not os.path.exists(struct_path):
        raise FileNotFoundError(f"Structural metrics file not found: {struct_path}")
    if not os.path.exists(dyn_path):
        raise FileNotFoundError(f"Dynamic metrics file not found: {dyn_path}")
        
    structural_df = pd.read_csv(struct_path)
    dynamic_df = pd.read_csv(dyn_path)
    
    # Run analysis
    results_df = run_correlation_analysis(structural_df, dynamic_df)
    
    # Save results
    output_path = config['paths']['correlation_results']
    results_df.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    print(f"Total correlations tested: {len(results_df)}")
    print(f"Significant findings (FDR < 0.05): {results_df['significant'].sum()}")

if __name__ == "__main__":
    main()