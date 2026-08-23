import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings
import os

def check_normality(data: pd.Series, alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: pandas Series to test
        alpha: significance level
        
    Returns:
        Tuple of (is_normal, p_value)
    """
    if len(data) < 3:
        return False, 0.0
        
    try:
        stat, p_value = shapiro(data)
        is_normal = p_value > alpha
        return is_normal, p_value
    except Exception:
        return False, 0.0

def calculate_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Calculate correlation between two series based on normality.
    
    Args:
        x: First series
        y: Second series
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    x_normal, _ = check_normality(x)
    y_normal, _ = check_normality(y)
    
    if x_normal and y_normal:
        try:
            r, p = pearsonr(x, y)
            return r, p
        except Exception:
            return 0.0, 1.0
    else:
        try:
            r, p = spearmanr(x, y)
            return r, p
        except Exception:
            return 0.0, 1.0

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of raw p-values
        alpha: FDR significance level
        
    Returns:
        List of booleans indicating if each test is significant after FDR correction
    """
    n = len(p_values)
    if n == 0:
        return []
        
    # Create index array
    indices = list(range(n))
    
    # Sort p-values while keeping track of original indices
    sorted_indices = sorted(indices, key=lambda i: p_values[i])
    sorted_pvals = [p_values[i] for i in sorted_indices]
    
    # Calculate BH critical values
    critical_values = [(i + 1) * alpha / n for i in range(n)]
    
    # Find the largest k such that p_(k) <= critical value
    significant = [False] * n
    max_k = -1
    
    for i in range(n - 1, -1, -1):
        if sorted_pvals[i] <= critical_values[i]:
            max_k = i
            break
    
    # Mark all tests up to max_k as significant
    if max_k >= 0:
        for i in range(max_k + 1):
            original_idx = sorted_indices[i]
            significant[original_idx] = True
            
    return significant

def run_correlation_analysis(structural_df: pd.DataFrame, dynamic_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run correlation analysis between structural and dynamic metrics.
    
    Args:
        structural_df: DataFrame with structural metrics
        dynamic_df: DataFrame with dynamic metrics
        
    Returns:
        DataFrame with correlation results including r, p, and FDR significance
    """
    # Merge on subject_id
    merged = pd.merge(structural_df, dynamic_df, on='subject_id', how='inner')
    
    if len(merged) < 3:
        raise ValueError("Insufficient subjects for correlation analysis (need at least 3)")
    
    # Define metrics to correlate
    structural_metrics = ['global_efficiency', 'avg_clustering', 'modularity']
    dynamic_metrics = ['dwell_time', 'visited_states']
    
    results = []
    
    for s_metric in structural_metrics:
        if s_metric not in merged.columns:
            continue
            
        for d_metric in dynamic_metrics:
            if d_metric not in merged.columns:
                continue
                
            x = merged[s_metric].dropna()
            y = merged[d_metric].dropna()
            
            # Align indices after dropping NaNs
            common_idx = x.index.intersection(y.index)
            if len(common_idx) < 3:
                continue
                
            x_aligned = x.loc[common_idx]
            y_aligned = y.loc[common_idx]
            
            r, p = calculate_correlation(x_aligned, y_aligned)
            
            results.append({
                'structural_metric': s_metric,
                'dynamic_metric': d_metric,
                'r_value': r,
                'p_value': p,
                'n_subjects': len(common_idx)
            })
    
    if not results:
        raise ValueError("No valid correlations could be computed")
        
    results_df = pd.DataFrame(results)
    
    # Apply FDR correction
    p_values = results_df['p_value'].tolist()
    fdr_significant = benjamini_hochberg_fdr(p_values, alpha=0.05)
    results_df['fdr_significant'] = fdr_significant
    
    return results_df

def main():
    """Main entry point for correlation analysis."""
    import sys
    from pathlib import Path
    
    # Determine paths relative to project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed'
    
    structural_path = data_dir / 'structural_metrics.csv'
    dynamic_path = data_dir / 'dynamic_metrics.csv'
    output_path = data_dir / 'correlation_results.csv'
    
    if not structural_path.exists():
        print(f"Error: Structural metrics file not found: {structural_path}", file=sys.stderr)
        sys.exit(1)
        
    if not dynamic_path.exists():
        print(f"Error: Dynamic metrics file not found: {dynamic_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        structural_df = pd.read_csv(structural_path)
        dynamic_df = pd.read_csv(dynamic_path)
        
        results_df = run_correlation_analysis(structural_df, dynamic_df)
        
        # Check for zero significant findings and add explicit note
        significant_count = results_df['fdr_significant'].sum()
        if significant_count == 0:
            print("WARNING: FDR correction yielded zero significant findings.", file=sys.stderr)
            print("This will be explicitly noted in the final report.", file=sys.stderr)
            # Add a column to indicate the overall finding status
            results_df['zero_significant_findings_note'] = "FDR correction (q=0.05) yielded no significant correlations between structural and dynamic metrics."
        
        results_df.to_csv(output_path, index=False)
        print(f"Correlation results saved to: {output_path}")
        print(f"Total correlations tested: {len(results_df)}")
        print(f"Significant after FDR: {significant_count}")
        
    except Exception as e:
        print(f"Error running correlation analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
