import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy import stats
import json
from pathlib import Path

def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute Mean Absolute Error.
    
    Args:
        y_true: Ground truth values (array-like)
        y_pred: Predicted values (array-like)
        
    Returns:
        MAE value (float)
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
    return float(np.mean(np.abs(y_true - y_pred)))

def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute R-squared (coefficient of determination).
    
    Args:
        y_true: Ground truth values (array-like)
        y_pred: Predicted values (array-like)
        
    Returns:
        R² value (float)
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0 if ss_res == 0 else -np.inf
        
    return float(1 - (ss_res / ss_tot))

def compute_metrics_per_property(y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    """
    Compute MAE and R² for each property in the dictionary.
    
    Args:
        y_true: Dictionary mapping property names to ground truth arrays
        y_pred: Dictionary mapping property names to predicted arrays
        
    Returns:
        Nested dictionary: {property_name: {'mae': float, 'r2': float}}
    """
    results = {}
    for prop in y_true.keys():
        if prop not in y_pred:
            raise KeyError(f"Property '{prop}' missing from predictions")
        
        mae = compute_mae(y_true[prop], y_pred[prop])
        r2 = compute_r2(y_true[prop], y_pred[prop])
        results[prop] = {'mae': mae, 'r2': r2}
        
    return results

def paired_ttest_mean_zero(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Perform a paired-sample t-test to check if the mean error is significantly different from zero.
    Null hypothesis (H0): The mean of the differences (errors) is zero.
    Alternative hypothesis (H1): The mean of the differences is not zero.
    
    This corresponds to Primary Validation per SC-003.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        Dictionary containing 't_statistic' and 'p_value'
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
    
    errors = y_pred - y_true
    
    # Perform one-sample t-test on errors against 0
    t_stat, p_val = stats.ttest_1samp(errors, 0.0)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val)
    }

def tost_equivalence_test(y_true: np.ndarray, y_pred: np.ndarray, equivalence_margin: float) -> Dict[str, float]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.
    
    Null hypothesis (H0): The mean difference is outside the equivalence interval [-margin, +margin].
    Alternative hypothesis (H1): The mean difference is inside the equivalence interval.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        equivalence_margin: The maximum acceptable difference for equivalence
        
    Returns:
        Dictionary containing 't_statistic_lower', 'p_value_lower', 't_statistic_upper', 'p_value_upper',
        'equivalent': True if both p-values < 0.05
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
    errors = y_pred - y_true
    n = len(errors)
    mean_err = np.mean(errors)
    std_err = np.std(errors, ddof=1)
    
    if std_err == 0:
        # If no variance, check if mean is exactly within bounds
        is_equiv = abs(mean_err) < equivalence_margin
        return {
            't_statistic_lower': 0.0,
            'p_value_lower': 0.0 if is_equiv else 1.0,
            't_statistic_upper': 0.0,
            'p_value_upper': 0.0 if is_equiv else 1.0,
            'equivalent': is_equiv
        }
    
    # T1: H0: mean <= -margin vs H1: mean > -margin
    # t = (mean - (-margin)) / (std / sqrt(n))
    t_lower = (mean_err - (-equivalence_margin)) / (std_err / np.sqrt(n))
    p_lower = 1 - stats.t.cdf(t_lower, df=n-1)
    
    # T2: H0: mean >= +margin vs H1: mean < +margin
    # t = (mean - margin) / (std / sqrt(n))
    t_upper = (mean_err - equivalence_margin) / (std_err / np.sqrt(n))
    p_upper = stats.t.cdf(t_upper, df=n-1)
    
    return {
        't_statistic_lower': float(t_lower),
        'p_value_lower': float(p_lower),
        't_statistic_upper': float(t_upper),
        'p_value_upper': float(p_upper),
        'equivalent': bool(p_lower < 0.05 and p_upper < 0.05)
    }

def hotellings_t2_test(y_true: np.ndarray, y_pred: np.ndarray, reference_mean: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Perform Hotelling's T² test for multivariate mean difference.
    
    This tests if the vector of errors has a mean significantly different from zero (or a reference).
    Useful for joint testing of multiple properties.
    
    Args:
        y_true: Ground truth values (2D array: samples x properties) OR 1D for single property
        y_pred: Predicted values (2D array: samples x properties) OR 1D for single property
        reference_mean: Optional reference mean vector (default: zeros)
        
    Returns:
        Dictionary containing 't2_statistic', 'f_statistic', 'p_value'
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")
        
    errors = y_pred - y_true
    
    # Handle 1D case (single property)
    if errors.ndim == 1:
        errors = errors.reshape(-1, 1)
        
    n_samples, n_features = errors.shape
    
    if reference_mean is None:
        reference_mean = np.zeros(n_features)
    else:
        reference_mean = np.asarray(reference_mean)
        
    if reference_mean.shape[0] != n_features:
        raise ValueError(f"Reference mean shape mismatch: {reference_mean.shape[0]} vs {n_features}")
    
    mean_diff = np.mean(errors, axis=0)
    diff_centered = errors - mean_diff
    
    # Covariance matrix
    cov_matrix = np.cov(diff_centered, rowvar=False)
    
    # Handle singular covariance (n < p)
    if n_samples <= n_features or np.linalg.matrix_rank(cov_matrix) < n_features:
        # Fallback to univariate test on first dimension or return NaN
        return {
            't2_statistic': float('nan'),
            'f_statistic': float('nan'),
            'p_value': float('nan'),
            'note': 'Singular covariance matrix (n_samples <= n_features)'
        }
    
    try:
        cov_inv = np.linalg.inv(cov_matrix)
    except np.linalg.LinAlgError:
        return {
            't2_statistic': float('nan'),
            'f_statistic': float('nan'),
            'p_value': float('nan'),
            'note': 'Covariance matrix is singular'
        }
    
    # Hotelling's T²
    diff_vec = mean_diff - reference_mean
    t2 = n_samples * np.dot(diff_vec, np.dot(cov_inv, diff_vec))
    
    # Convert to F-statistic
    # F = (n - p) / (p * (n - 1)) * T²
    # df1 = p, df2 = n - p
    f_stat = ((n_samples - n_features) / (n_features * (n_samples - 1))) * t2
    p_val = 1 - stats.f.cdf(f_stat, dfn=n_features, dfd=n_samples - n_features)
    
    return {
        't2_statistic': float(t2),
        'f_statistic': float(f_stat),
        'p_value': float(p_val)
    }

def compute_all_statistics(y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray], 
                           equivalence_margin: float = 0.1,
                           reference_mean: Optional[np.ndarray] = None) -> Dict[str, any]:
    """
    Compute all statistical metrics: MAE, R², Paired T-test, TOST, and Hotelling's T².
    
    Args:
        y_true: Dictionary of ground truth arrays
        y_pred: Dictionary of predicted arrays
        equivalence_margin: Margin for TOST test
        reference_mean: Reference mean for Hotelling's T² (if None, uses zeros)
        
    Returns:
        Comprehensive dictionary of all computed statistics
    """
    results = {
        'metrics': compute_metrics_per_property(y_true, y_pred),
        'paired_ttests': {},
        'tost_tests': {},
        'hotellings_t2': {}
    }
    
    # Compute per-property tests
    for prop in y_true.keys():
        yt = y_true[prop]
        yp = y_pred[prop]
        
        # Paired t-test
        results['paired_ttests'][prop] = paired_ttest_mean_zero(yt, yp)
        
        # TOST
        results['tost_tests'][prop] = tost_equivalence_test(yt, yp, equivalence_margin)
    
    # Multivariate Hotelling's T² (if multiple properties)
    if len(y_true) > 1:
        # Stack arrays
        properties = list(y_true.keys())
        y_true_stacked = np.column_stack([y_true[p] for p in properties])
        y_pred_stacked = np.column_stack([y_pred[p] for p in properties])
        
        results['hotellings_t2'] = hotellings_t2_test(y_true_stacked, y_pred_stacked, reference_mean)
    else:
        results['hotellings_t2'] = {
            't2_statistic': float('nan'),
            'f_statistic': float('nan'),
            'p_value': float('nan'),
            'note': 'Single property - multivariate test not applicable'
        }
        
    return results

def main():
    """
    CLI entry point for metrics computation.
    Loads test data, runs model inference (placeholder), and computes statistics.
    """
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Compute evaluation metrics and statistical tests')
    parser.add_argument('--y_true', type=str, required=True, help='Path to ground truth data (npz)')
    parser.add_argument('--y_pred', type=str, required=True, help='Path to predicted data (npz)')
    parser.add_argument('--output', type=str, default='results/evaluation_metrics.json', help='Output JSON path')
    parser.add_argument('--equivalence_margin', type=float, default=0.1, help='Margin for TOST')
    
    args = parser.parse_args()
    
    # Load data
    y_true_data = np.load(args.y_true)
    y_pred_data = np.load(args.y_pred)
    
    y_true_dict = {k: y_true_data[k] for k in y_true_data.files}
    y_pred_dict = {k: y_pred_data[k] for k in y_pred_data.files}
    
    # Compute statistics
    stats_results = compute_all_statistics(y_true_dict, y_pred_dict, args.equivalence_margin)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats_results, f, indent=2)
        
    print(f"Results saved to {output_path}")
    return stats_results

if __name__ == '__main__':
    main()