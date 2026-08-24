import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy import stats
import json
from pathlib import Path

def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))

def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute R-squared (coefficient of determination)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - (ss_res / ss_tot))

def compute_metrics_per_property(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    property_names: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Compute MAE and R2 for each property.
    
    Args:
        y_true: Array of shape (N, num_properties)
        y_pred: Array of shape (N, num_properties)
        property_names: List of property names
        
    Returns:
        Dictionary mapping property names to metrics
    """
    results = {}
    for i, name in enumerate(property_names):
        if i < y_true.shape[1] and i < y_pred.shape[1]:
            results[name] = {
                "mae": compute_mae(y_true[:, i], y_pred[:, i]),
                "r2": compute_r2(y_true[:, i], y_pred[:, i])
            }
    return results

def paired_ttest_mean_zero(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """
    Perform a paired t-test with null hypothesis: mean error = 0.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    errors = y_pred - y_true
    t_stat, p_val = stats.ttest_1samp(errors, 0.0)
    return float(t_stat), float(p_val)

def tost_equivalence_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    equivalence_margin: float = 0.1
) -> Tuple[float, float, bool]:
    """
    Perform TOST (Two One-Sided Tests) for equivalence.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        equivalence_margin: Margin for equivalence
        
    Returns:
        Tuple of (t_stat_lower, t_stat_upper, is_equivalent)
    """
    errors = y_pred - y_true
    
    # Test 1: H0: mean_error >= -margin vs Ha: mean_error < -margin
    t_lower, p_lower = stats.ttest_1samp(errors, -equivalence_margin)
    # We want the one-sided p-value for the lower tail
    # ttest_1samp returns two-sided, so we adjust
    # Actually, for TOST we use ttest_1samp with the margin as the mu
    # But scipy's ttest_1samp is for mean == mu.
    # Let's use the standard approach:
    # t1 = (mean - (-margin)) / se
    # t2 = (mean - margin) / se
    # We want p(t1 < t_crit) and p(t2 > t_crit)
    
    # Re-implementing manually for clarity
    n = len(errors)
    mean_err = np.mean(errors)
    std_err = np.std(errors, ddof=1)
    se = std_err / np.sqrt(n)
    
    t1 = (mean_err - (-equivalence_margin)) / se
    t2 = (mean_err - equivalence_margin) / se
    
    # One-sided p-values
    # t1: test if mean > -margin (we want to reject H0: mean <= -margin)
    # Actually, TOST:
    # H0_1: mean <= -margin (reject if t1 is large positive? No, t1 = (mean - (-margin))/se)
    # If mean is significantly greater than -margin, t1 is large positive.
    # We want p(t > t1) for the upper tail of the null distribution?
    # Let's stick to the standard interpretation:
    # Reject H0_1 (mean <= -margin) if t1 > t_crit
    # Reject H0_2 (mean >= margin) if t2 < -t_crit
    
    # Using scipy's ttest_1samp for one-sided:
    # For H0: mean = -margin, we want to see if mean > -margin.
    # t_stat = (mean - (-margin)) / se
    # p_value = 1 - CDF(t_stat) if t_stat > 0 else CDF(t_stat)
    # But ttest_1samp returns two-sided.
    
    # Let's use the direct calculation
    from scipy.stats import t
    df = n - 1
    
    p1 = 1 - t.cdf(t1, df) # Prob(t > t1)
    p2 = t.cdf(t2, df)     # Prob(t < t2)
    
    # Equivalence if both p1 and p2 are small (e.g., < 0.05)
    is_equivalent = (p1 < 0.05) and (p2 < 0.05)
    
    return float(t1), float(t2), is_equivalent

def hotellings_t2_test(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """
    Perform Hotelling's T-squared test for multivariate mean difference.
    (Simplified implementation for 3 properties)
    
    Args:
        y_true: True values (N, 3)
        y_pred: Predicted values (N, 3)
        
    Returns:
        Tuple of (t2_statistic, p_value)
    """
    errors = y_pred - y_true
    n = errors.shape[0]
    p = errors.shape[1] # number of variables
    
    mean_err = np.mean(errors, axis=0)
    cov_err = np.cov(errors, rowvar=False)
    
    if np.linalg.matrix_rank(cov_err) < p:
        # Singular covariance, cannot compute T2
        return 0.0, 1.0
        
    cov_inv = np.linalg.inv(cov_err)
    
    # T2 = n * mean' * cov^-1 * mean
    t2 = n * mean_err @ cov_inv @ mean_err
    
    # Convert to F-statistic: F = (n-p) / (p*(n-1)) * T2
    f_stat = ((n - p) / (p * (n - 1))) * t2
    
    # P-value from F-distribution
    p_val = 1 - stats.f.cdf(f_stat, p, n - p)
    
    return float(t2), float(p_val)

def compute_all_statistics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    return_dict: bool = True
) -> Dict[str, float]:
    """
    Compute all relevant statistics (MAE, R2, T-test, TOST, Hotelling's).
    
    Args:
        y_true: True values
        y_pred: Predicted values
        return_dict: If True, return a dictionary; else return a tuple
        
    Returns:
        Dictionary or Tuple of statistics
    """
    mae = compute_mae(y_true, y_pred)
    r2 = compute_r2(y_true, y_pred)
    t_stat, p_val = paired_ttest_mean_zero(y_true, y_pred)
    
    result = {
        "mae": mae,
        "r2": r2,
        "t_statistic": t_stat,
        "p_value": p_val
    }
    
    if return_dict:
        return result
    else:
        return mae, r2, t_stat, p_val

def main():
    """
    Main entry point for metrics module (for testing).
    """
    # Example usage
    y_true = np.random.rand(100)
    y_pred = y_true + np.random.normal(0, 0.1, 100)
    
    metrics = compute_all_statistics(y_true, y_pred)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()