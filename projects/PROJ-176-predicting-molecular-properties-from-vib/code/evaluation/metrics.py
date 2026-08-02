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
    y_true: Dict[str, np.ndarray],
    y_pred: Dict[str, np.ndarray]
) -> Dict[str, Dict[str, float]]:
    """Compute MAE and R2 for each property."""
    results = {}
    for prop in y_true.keys():
        if prop in y_pred:
            results[prop] = {
                "mae": compute_mae(y_true[prop], y_pred[prop]),
                "r2": compute_r2(y_true[prop], y_pred[prop])
            }
    return results

def paired_ttest_mean_zero(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Perform paired-sample t-test to check if mean error is zero.
    Null hypothesis: mean(error) = 0.
    """
    errors = y_true - y_pred
    t_stat, p_val = stats.ttest_1samp(errors, 0.0)
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_error": float(np.mean(errors)),
        "std_error": float(np.std(errors))
    }

def tost_equivalence_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    equivalence_margin: float = 0.1,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.
    Null hypothesis: |mean(error)| >= equivalence_margin.
    Alternative hypothesis: |mean(error)| < equivalence_margin.
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        equivalence_margin: The margin (delta) for equivalence.
        alpha: Significance level.
    
    Returns:
        Dictionary with p-values for both one-sided tests and equivalence conclusion.
    """
    errors = y_true - y_pred
    n = len(errors)
    mean_err = np.mean(errors)
    std_err = np.std(errors, ddof=1)
    
    if std_err == 0:
        # If no variance, check if mean is within margin
        is_equivalent = abs(mean_err) < equivalence_margin
        return {
            "p_value_lower": 1.0 if mean_err >= -equivalence_margin else 0.0,
            "p_value_upper": 1.0 if mean_err <= equivalence_margin else 0.0,
            "is_equivalent": is_equivalent,
            "mean_error": float(mean_err),
            "equivalence_margin": equivalence_margin
        }

    # T-test for lower bound: H0: mean <= -delta
    # We test if mean > -delta
    t_lower = (mean_err - (-equivalence_margin)) / (std_err / np.sqrt(n))
    p_lower = 1 - stats.t.cdf(t_lower, df=n-1)

    # T-test for upper bound: H0: mean >= delta
    # We test if mean < delta
    t_upper = (mean_err - equivalence_margin) / (std_err / np.sqrt(n))
    p_upper = stats.t.cdf(t_upper, df=n-1)

    # Equivalence is concluded if both p-values < alpha
    is_equivalent = (p_lower < alpha) and (p_upper < alpha)

    return {
        "p_value_lower": float(p_lower),
        "p_value_upper": float(p_upper),
        "is_equivalent": is_equivalent,
        "mean_error": float(mean_err),
        "equivalence_margin": equivalence_margin,
        "alpha": alpha
    }

def hotellings_t2_test(
    y_true_dict: Dict[str, np.ndarray],
    y_pred_dict: Dict[str, np.ndarray],
    reference_mean: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Perform Hotelling's T-squared test for multivariate mean difference.
    Tests if the mean vector of errors is significantly different from zero (or reference).
    
    Args:
        y_true_dict: Dictionary of ground truth arrays (keys = properties).
        y_pred_dict: Dictionary of predicted arrays (keys = properties).
        reference_mean: Optional reference mean vector (default: zero vector).
    
    Returns:
        Dictionary with T-squared statistic, p-value, and degrees of freedom.
    """
    # Ensure all properties are aligned
    properties = sorted(y_true_dict.keys())
    if not all(p in y_pred_dict for p in properties):
        raise ValueError("All properties in y_true_dict must be present in y_pred_dict")
    
    # Stack errors into a 2D array (n_samples x n_properties)
    errors = np.column_stack([y_true_dict[p] - y_pred_dict[p] for p in properties])
    n_samples, n_vars = errors.shape
    
    if n_samples <= n_vars:
        # Not enough samples for Hotelling's T2
        return {
            "t2_statistic": float('inf'),
            "p_value": 0.0,
            "df1": n_vars,
            "df2": n_samples - n_vars,
            "note": "Insufficient samples for Hotelling's T2 (n <= p)"
        }
    
    # Mean error vector
    mean_error = np.mean(errors, axis=0)
    
    # Covariance matrix of errors
    cov_matrix = np.cov(errors, rowvar=False)
    
    # Handle singular covariance matrix
    try:
        cov_inv = np.linalg.inv(cov_matrix)
    except np.linalg.LinAlgError:
        # Use pseudo-inverse if singular
        cov_inv = np.linalg.pinv(cov_matrix)
    
    # Hotelling's T-squared statistic
    # T^2 = n * (mean - mu0)' * S^-1 * (mean - mu0)
    mean_diff = mean_error - (reference_mean if reference_mean is not None else np.zeros(n_vars))
    t2 = n_samples * np.dot(mean_diff.T, np.dot(cov_inv, mean_diff))
    
    # Convert to F-statistic for p-value calculation
    # F = ((n - p) / (p * (n - 1))) * T^2
    # df1 = p, df2 = n - p
    df1 = n_vars
    df2 = n_samples - n_vars
    f_stat = ((n_samples - n_vars) / (n_vars * (n_samples - 1))) * t2
    
    # P-value from F-distribution
    p_val = 1 - stats.f.cdf(f_stat, df1, df2)
    
    return {
        "t2_statistic": float(t2),
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "df1": df1,
        "df2": df2,
        "n_samples": n_samples,
        "n_properties": n_vars,
        "mean_error_vector": mean_error.tolist()
    }

def compute_all_statistics(
    y_true: Dict[str, np.ndarray],
    y_pred: Dict[str, np.ndarray],
    equivalence_margin: float = 0.1,
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Compute all statistical metrics: MAE, R2, paired t-test, TOST, Hotelling's T2.
    
    Args:
        y_true: Dictionary of ground truth arrays.
        y_pred: Dictionary of predicted arrays.
        equivalence_margin: Margin for TOST equivalence test.
        alpha: Significance level for TOST.
    
    Returns:
        Dictionary containing all computed statistics.
    """
    results = {}
    
    # Per-property metrics
    results["per_property"] = compute_metrics_per_property(y_true, y_pred)
    
    # Paired t-tests for each property
    results["paired_ttests"] = {}
    for prop in y_true.keys():
        if prop in y_pred:
            results["paired_ttests"][prop] = paired_ttest_mean_zero(
                y_true[prop], y_pred[prop]
            )
    
    # TOST for each property
    results["tost_equivalence"] = {}
    for prop in y_true.keys():
        if prop in y_pred:
            results["tost_equivalence"][prop] = tost_equivalence_test(
                y_true[prop], y_pred[prop],
                equivalence_margin=equivalence_margin,
                alpha=alpha
            )
    
    # Multivariate Hotelling's T2 test
    results["hotellings_t2"] = hotellings_t2_test(y_true, y_pred)
    
    return results

def main():
    """
    Example usage of the statistical evaluation functions.
    This can be run as a standalone script to demonstrate functionality.
    """
    # Example data (in real usage, this would come from model predictions and test set)
    np.random.seed(42)
    n_samples = 100
    
    y_true_example = {
        "dipole": np.random.normal(0, 1, n_samples),
        "polarizability": np.random.normal(0, 1, n_samples),
        "homo_lumo_gap": np.random.normal(0, 1, n_samples)
    }
    
    # Simulate predictions with some error
    y_pred_example = {
        "dipole": y_true_example["dipole"] + np.random.normal(0, 0.1, n_samples),
        "polarizability": y_true_example["polarizability"] + np.random.normal(0, 0.1, n_samples),
        "homo_lumo_gap": y_true_example["homo_lumo_gap"] + np.random.normal(0, 0.1, n_samples)
    }
    
    # Compute all statistics
    stats_results = compute_all_statistics(y_true_example, y_pred_example)
    
    # Print results
    print("Statistical Evaluation Results:")
    print(json.dumps(stats_results, indent=2))
    
    return stats_results

if __name__ == "__main__":
    main()