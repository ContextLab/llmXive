"""
Statistical testing and correlation analysis module.

Implements normality testing, correlation calculation (Pearson/Spearman),
and Benjamini-Hochberg FDR correction for structure-function analysis.
"""
import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings

# Suppress specific warnings for cleaner output if needed
warnings.filterwarnings('ignore', category=RuntimeWarning)


def check_normality(data: np.ndarray, alpha: float = 0.05) -> Tuple[bool, float, float]:
    """
    Perform Shapiro-Wilk normality test on a 1D array of data.
    
    Args:
        data: 1D numpy array of values.
        alpha: Significance level for the test (default 0.05).
        
    Returns:
        Tuple of (is_normal, statistic, p_value).
        is_normal is True if p_value > alpha (fail to reject null hypothesis).
    """
    if len(data) < 3:
        # Shapiro-Wilk requires at least 3 samples
        return False, 0.0, 0.0
        
    statistic, p_value = shapiro(data)
    is_normal = p_value > alpha
    return is_normal, statistic, p_value


def calculate_correlation(
    x: np.ndarray,
    y: np.ndarray,
    alpha: float = 0.05
) -> Tuple[float, float, str]:
    """
    Calculate correlation between two 1D arrays, selecting method based on normality.
    
    Args:
        x: First 1D numpy array.
        y: Second 1D numpy array (must be same length as x).
        alpha: Significance level for normality test (default 0.05).
        
    Returns:
        Tuple of (correlation_coefficient, p_value, method_used).
        method_used is either 'pearson' or 'spearman'.
    """
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("Arrays must be non-empty, same length, and have at least 3 elements.")
        
    # Check normality for both variables
    x_normal, _, _ = check_normality(x, alpha)
    y_normal, _, _ = check_normality(y, alpha)
    
    # Use Pearson if both are normal, otherwise Spearman
    if x_normal and y_normal:
        corr, p_val = pearsonr(x, y)
        method = 'pearson'
    else:
        corr, p_val = spearmanr(x, y)
        method = 'spearman'
        
    return float(corr), float(p_val), method


def benjamini_hochberg_fdr(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: FDR significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, is_significant).
        adjusted_p_values is a list of FDR-corrected p-values.
        is_significant is a list of booleans indicating significance after correction.
    """
    if not p_values:
        return [], []
        
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH adjusted p-values
    # Formula: p_adj = p_i * n / i, then enforce monotonicity
    ranks = np.arange(1, n + 1)
    adjusted = (sorted_p_values * n) / ranks
    
    # Enforce monotonicity (cumulative min from the end)
    # This ensures p_adj(i) <= p_adj(i+1)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
        
    # Clamp to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    # Restore original order
    original_order_adjusted = np.zeros(n)
    original_order_adjusted[sorted_indices] = adjusted
    
    # Determine significance
    is_sig = original_order_adjusted < alpha
    
    return original_order_adjusted.tolist(), is_sig.tolist()


def run_correlation_analysis(
    structural_metrics: pd.DataFrame,
    dynamic_metrics: pd.DataFrame,
    structural_columns: List[str],
    dynamic_columns: List[str],
    alpha: float = 0.05,
    fdr_alpha: float = 0.05
) -> pd.DataFrame:
    """
    Perform correlation analysis between structural and dynamic metrics.
    
    Args:
        structural_metrics: DataFrame with structural metrics (rows=subjects).
        dynamic_metrics: DataFrame with dynamic metrics (rows=subjects).
        structural_columns: List of column names from structural_metrics to test.
        dynamic_columns: List of column names from dynamic_metrics to test.
        alpha: Significance level for normality/correlation tests.
        fdr_alpha: Significance level for FDR correction.
        
    Returns:
        DataFrame with columns: struct_metric, dyn_metric, r_value, p_value, 
        method, fdr_p_value, is_significant.
    """
    # Ensure subject alignment (assume same index order)
    if not structural_metrics.index.equals(dynamic_metrics.index):
        # If indices don't match, try to align by index or assume row order
        if structural_metrics.shape[0] != dynamic_metrics.shape[0]:
            raise ValueError("Structural and dynamic metrics must have same number of subjects.")
        
    results = []
    
    all_p_values = []
    all_results = []
    
    for s_col in structural_columns:
        for d_col in dynamic_columns:
            x = structural_metrics[s_col].values
            y = dynamic_metrics[d_col].values
            
            # Remove NaN pairs
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) < 3:
                # Not enough data points
                results.append({
                    'struct_metric': s_col,
                    'dyn_metric': d_col,
                    'r_value': np.nan,
                    'p_value': np.nan,
                    'method': 'insufficient_data',
                    'fdr_p_value': np.nan,
                    'is_significant': False
                })
                continue
                
            r, p, method = calculate_correlation(x_clean, y_clean, alpha)
            
            all_p_values.append(p)
            all_results.append({
                'struct_metric': s_col,
                'dyn_metric': d_col,
                'r_value': r,
                'p_value': p,
                'method': method
            })
    
    # Apply FDR correction to all valid p-values
    if all_p_values:
        fdr_p_values, is_sig = benjamini_hochberg_fdr(all_p_values, fdr_alpha)
        
        # Merge FDR results back
        for i, res in enumerate(all_results):
            res['fdr_p_value'] = fdr_p_values[i]
            res['is_significant'] = is_sig[i]
            results.append(res)
    else:
        # No valid correlations to correct
        for res in all_results:
            res['fdr_p_value'] = np.nan
            res['is_significant'] = False
            results.append(res)
            
    return pd.DataFrame(results)


def main():
    """
    Example usage for testing the correlation module.
    This function is not executed automatically; it serves as documentation.
    """
    # Sample data for demonstration
    np.random.seed(42)
    n_subjects = 50
    
    # Generate sample structural and dynamic metrics
    struct_data = pd.DataFrame({
        'global_efficiency': np.random.normal(0.4, 0.1, n_subjects),
        'clustering_coef': np.random.normal(0.3, 0.05, n_subjects),
        'modularity': np.random.normal(0.5, 0.1, n_subjects)
    })
    
    dyn_data = pd.DataFrame({
        'dwell_time': np.random.normal(100, 20, n_subjects),
        'n_states': np.random.normal(5, 1, n_subjects)
    })
    
    # Run analysis
    results = run_correlation_analysis(
        struct_data,
        dyn_data,
        ['global_efficiency', 'clustering_coef'],
        ['dwell_time', 'n_states'],
        alpha=0.05,
        fdr_alpha=0.05
    )
    
    print("Correlation Analysis Results:")
    print(results)
    
    return results


if __name__ == "__main__":
    main()