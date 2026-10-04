"""
Metrics and statistical tests for model evaluation.
Implements MAE, R², paired t-tests, TOST, and Hotelling's T² tests.
"""
import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy import stats
import json
from pathlib import Path

def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute Mean Absolute Error.

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        MAE value.
    """
    return np.mean(np.abs(y_true - y_pred))

def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute R² (coefficient of determination).

    Args:
        y_true: True values.
        y_pred: Predicted values.

    Returns:
        R² value.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

def compute_metrics_per_property(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    property_names: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Compute MAE and R² for each property.

    Args:
        y_true: True values (n_samples, n_properties).
        y_pred: Predicted values (n_samples, n_properties).
        property_names: Names of the properties.

    Returns:
        Dictionary with metrics for each property.
    """
    results = {}
    for i, prop_name in enumerate(property_names):
        results[prop_name] = {
            "mae": float(compute_mae(y_true[:, i], y_pred[:, i])),
            "r2": float(compute_r2(y_true[:, i], y_pred[:, i]))
        }
    return results

def paired_ttest_mean_zero(
    errors: np.ndarray,
    alpha: float = 0.01
) -> Tuple[float, bool]:
    """
    Perform paired-sample t-test to check if mean error is zero.
    Null hypothesis: mean error = 0 (no systematic bias).

    Args:
        errors: Array of errors (predicted - true).
        alpha: Significance level.

    Returns:
        Tuple of (p_value, bias_pass_fail).
        bias_pass_fail is True if p >= alpha (no significant bias), False otherwise.
    """
    t_stat, p_value = stats.ttest_1samp(errors, 0.0)
    bias_pass_fail = p_value >= alpha
    return float(p_value), bias_pass_fail

def tost_equivalence_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    equivalence_margin: float = 0.1,
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.

    Args:
        y_true: True values.
        y_pred: Predicted values.
        equivalence_margin: Margin for equivalence.
        alpha: Significance level.

    Returns:
        Tuple of (p_value_lower, p_value_upper, is_equivalent).
    """
    errors = y_pred - y_true
    n = len(errors)
    mean_error = np.mean(errors)
    std_error = np.std(errors, ddof=1)

    # TOST: test if mean is within [-margin, +margin]
    t_lower = (mean_error - (-equivalence_margin)) / (std_error / np.sqrt(n))
    t_upper = (mean_error - equivalence_margin) / (std_error / np.sqrt(n))

    p_lower = 1 - stats.t.cdf(t_lower, n - 1)
    p_upper = stats.t.cdf(t_upper, n - 1)

    is_equivalent = (p_lower < alpha) and (p_upper < alpha)

    return float(p_lower), float(p_upper), is_equivalent

def hotellings_t2_test(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Tuple[float, float]:
    """
    Perform Hotelling's T² test for multivariate mean difference.
    Tests if the mean error vector is zero.

    Args:
        y_true: True values (n_samples, n_properties).
        y_pred: Predicted values (n_samples, n_properties).

    Returns:
        Tuple of (t2_statistic, p_value).
    """
    errors = y_pred - y_true
    n, p = errors.shape

    mean_error = np.mean(errors, axis=0)
    cov_matrix = np.cov(errors, rowvar=False)

    # Add small regularization to avoid singular matrix
    cov_matrix += np.eye(p) * 1e-8

    try:
        cov_inv = np.linalg.inv(cov_matrix)
        t2 = n * mean_error @ cov_inv @ mean_error

        # Convert to F-statistic
        f_stat = ((n - p) / (p * (n - 1))) * t2
        df1 = p
        df2 = n - p

        p_value = 1 - stats.f.cdf(f_stat, df1, df2)
    except np.linalg.LinAlgError:
        # If matrix is singular, return large p-value
        t2 = float('inf')
        p_value = 1.0

    return float(t2), float(p_value)

def compute_all_statistics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    property_names: List[str],
    equivalence_margin: float = 0.1,
    ttest_alpha: float = 0.01
) -> Dict[str, Dict[str, Any]]:
    """
    Compute all statistical tests for all properties.

    Args:
        y_true: True values (n_samples, n_properties).
        y_pred: Predicted values (n_samples, n_properties).
        property_names: Names of the properties.
        equivalence_margin: Margin for TOST equivalence test.
        ttest_alpha: Significance level for t-test.

    Returns:
        Dictionary with all statistical test results.
    """
    results = {}

    for i, prop_name in enumerate(property_names):
        errors = y_pred[:, i] - y_true[:, i]

        # Paired t-test for systematic bias
        p_value_ttest, bias_pass_fail = paired_ttest_mean_zero(errors, alpha=ttest_alpha)

        # TOST for equivalence
        p_lower, p_upper, is_equivalent = tost_equivalence_test(
            y_true[:, i], y_pred[:, i],
            equivalence_margin=equivalence_margin
        )

        results[prop_name] = {
            "paired_ttest": {
                "p_value": p_value_ttest,
                "bias_pass_fail": bias_pass_fail,
                "alpha": ttest_alpha
            },
            "tost_equivalence": {
                "p_value_lower": p_lower,
                "p_value_upper": p_upper,
                "is_equivalent": is_equivalent,
                "equivalence_margin": equivalence_margin
            }
        }

    # Multivariate test (Hotelling's T²)
    t2_stat, p_value_hotelling = hotellings_t2_test(y_true, y_pred)
    results["multivariate"] = {
        "hotellings_t2": {
            "t2_statistic": t2_stat,
            "p_value": p_value_hotelling
        }
    }

    return results

def main():
    """
    Main entry point for the metrics module.
    """
    print("Metrics module loaded successfully.")
    print("Available functions:")
    print("  - compute_mae(y_true, y_pred)")
    print("  - compute_r2(y_true, y_pred)")
    print("  - compute_metrics_per_property(y_true, y_pred, property_names)")
    print("  - paired_ttest_mean_zero(errors, alpha)")
    print("  - tost_equivalence_test(y_true, y_pred, equivalence_margin, alpha)")
    print("  - hotellings_t2_test(y_true, y_pred)")
    print("  - compute_all_statistics(y_true, y_pred, property_names)")

if __name__ == "__main__":
    main()
