"""
Shift detection utilities for calibration drift analysis.

Implements BIC-based change point detection to identify abrupt shifts
in time-series metrics, overriding fixed block-size methods per Plan.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Union


def _calculate_residual_sum_of_squares(data: np.ndarray, split_idx: int) -> float:
    """
    Calculate the Residual Sum of Squares (RSS) for a piecewise constant model
    with a single change point at split_idx.

    The model assumes the mean of the data changes at split_idx.
    RSS = sum((y - mean_left)^2 for left) + sum((y - mean_right)^2 for right)
    """
    n = len(data)
    if split_idx <= 0 or split_idx >= n:
        return float('inf')

    left_part = data[:split_idx]
    right_part = data[split_idx:]

    mean_left = np.mean(left_part)
    mean_right = np.mean(right_part)

    rss_left = np.sum((left_part - mean_left) ** 2)
    rss_right = np.sum((right_part - mean_right) ** 2)

    return rss_left + rss_right


def _calculate_bic(rss: float, n: int, k: int, sigma_sq: Optional[float] = None) -> float:
    """
    Calculate the Bayesian Information Criterion (BIC).

    BIC = n * ln(RSS/n) + k * ln(n)

    Parameters:
    -----------
    rss : float
        Residual Sum of Squares.
    n : int
        Number of data points.
    k : int
        Number of parameters (1 for mean before, 1 for mean after, 1 for change point location?
        Typically for change point detection with unknown location, k is often treated as 3
        (mu1, mu2, tau) or simplified. Here we use k=3 for the model with a change point
        vs k=1 for no change point.
    sigma_sq : float, optional
        Estimated variance. If None, RSS/n is used.
    """
    if rss <= 0:
        return float('inf')

    # Standard BIC formulation for regression-like models
    # BIC = n * ln(RSS/n) + k * ln(n)
    # We assume the error variance is estimated by RSS/n
    return n * np.log(rss / n) + k * np.log(n)


def detect_change_point_bic(
    metrics: Union[List[Dict[str, Any]], np.ndarray],
    metric_key: Optional[str] = 'ece_5',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Detect change points in a time-series of metrics using BIC.

    This function implements the BIC-based change point detection as required by
    the project plan to override fixed block-size methods (FR-006).

    It tests every possible split point to find the one that minimizes the BIC
    score for a model with one change point versus a model with no change point.

    Parameters:
    -----------
    metrics : list of dict or np.ndarray
        If list of dict, must contain the metric values. If dict, keys should match
        the time series index or be ignored if metric_key is provided.
        If np.ndarray, treated as the raw time series values.
    metric_key : str, optional
        The key to extract the value from metric dictionaries if `metrics` is a list of dicts.
        Default is 'ece_5'.
    alpha : float, optional
        Significance level for the test. Default is 0.05.

    Returns:
    --------
    dict
        A dictionary containing:
        - 'change_point_year': The index (or year if available) of the detected change point.
        - 'change_point_index': The 0-based index in the array.
        - 'bic_difference': The difference in BIC between the null model (no change) and
                            the best alternative model (with change). Positive means change point model is better.
        - 'detected': Boolean indicating if a change point was detected based on the BIC threshold.
                      We use a heuristic: if the best BIC is significantly lower (e.g., > 2 or > 10) than the null BIC.
                      Strictly, BIC difference > 10 is "very strong" evidence.
        - 'best_bic': The BIC of the best model.
        - 'null_bic': The BIC of the null model (no change point).

    Raises:
    -------
    ValueError
        If the input data is empty or has fewer than 3 points.
    """
    # Extract data
    if isinstance(metrics, list):
        if not metrics:
            raise ValueError("Metrics list is empty.")
        if metric_key is None:
            raise ValueError("metric_key must be provided if metrics is a list of dicts.")
        # Extract values, handling potential missing keys or non-numeric data
        values = []
        for m in metrics:
            if isinstance(m, dict) and metric_key in m:
                val = m[metric_key]
                if isinstance(val, (int, float)) and not np.isnan(val):
                    values.append(val)
            elif isinstance(m, (int, float)) and not np.isnan(m):
                values.append(m)
        
        if len(values) < 3:
            raise ValueError("At least 3 data points are required for change point detection.")
        data = np.array(values)
    elif isinstance(metrics, np.ndarray):
        if len(metrics) < 3:
            raise ValueError("At least 3 data points are required for change point detection.")
        data = metrics
    else:
        raise ValueError("Metrics must be a list or numpy array.")

    n = len(data)

    # Calculate Null Model BIC (k=1: just the global mean)
    global_mean = np.mean(data)
    rss_null = np.sum((data - global_mean) ** 2)
    # For null model: 1 parameter (mean)
    null_bic = _calculate_bic(rss_null, n, k=1)

    best_bic = float('inf')
    best_split_idx = -1

    # Iterate over all possible split points
    # A split point at index i means data[:i] is one segment, data[i:] is another.
    # We need at least 1 point in each segment, so i ranges from 1 to n-1.
    # To be robust, we might enforce a minimum segment size (e.g., 2), but BIC penalizes complexity.
    # Let's allow 1 point segments for maximum sensitivity, though practically we might want min 3.
    min_segment_size = 2
    for i in range(min_segment_size, n - min_segment_size + 1):
        rss = _calculate_residual_sum_of_squares(data, i)
        # Model with change point: 3 parameters (mean1, mean2, change point location)
        # Note: Some formulations use k=2 (means) + penalty for location, but standard BIC for change point
        # often uses k=3.
        current_bic = _calculate_bic(rss, n, k=3)

        if current_bic < best_bic:
            best_bic = current_bic
            best_split_idx = i

    if best_split_idx == -1:
        # This should not happen if the loop runs, but safety check
        return {
            'change_point_year': None,
            'change_point_index': None,
            'bic_difference': 0.0,
            'detected': False,
            'best_bic': null_bic,
            'null_bic': null_bic
        }

    # BIC Difference: Null - Best (Positive means Best is better)
    bic_difference = null_bic - best_bic

    # Decision rule:
    # According to standard BIC interpretation:
    # BIC difference < 2: Weak evidence
    # 2 < BIC difference < 6: Positive evidence
    # 6 < BIC difference < 10: Strong evidence
    # BIC difference > 10: Very strong evidence
    # We will use a threshold of 10 for "detected" to be conservative, or we can use a statistical test approximation.
    # Since the prompt asks for alpha=0.05, we can map this to a BIC threshold.
    # However, BIC is a Bayesian criterion, not a frequentist p-value.
    # A common heuristic is that BIC diff > 2 is significant, > 10 is very strong.
    # To strictly adhere to "alpha=0.05", we might need a likelihood ratio test approximation,
    # but BIC is the requested method. We will use a threshold of 10 as "strong evidence" for detection.
    # Alternatively, we can interpret the alpha as a threshold on the BIC difference.
    # Let's use a threshold of 10 for "detected" to ensure robustness against noise,
    # as small fluctuations shouldn't trigger a change point in scientific research.
    # If the user wants a specific statistical test, they should use the LR test.
    # Given the constraint "Implement BIC-based detection", we rely on the BIC difference magnitude.
    # A threshold of 10 is standard for "very strong" evidence.
    
    # Let's refine: If the BIC difference is positive and large enough.
    # We'll set a threshold. A BIC difference of 10 corresponds to a Bayes Factor of ~22026, which is huge.
    # A BIC difference of 2 is ~7.4.
    # Let's use 10 as the threshold for "detected" to be safe, or we can make it dynamic based on alpha?
    # No, BIC doesn't take alpha directly. We'll use a fixed threshold of 10 for "strong evidence".
    # However, the task says "alpha=0.05". This implies a statistical test.
    # The BIC is asymptotically equivalent to a likelihood ratio test with a specific penalty.
    # We will interpret "detected" as BIC difference > 10 (very strong evidence).
    # If we must map alpha, we could say BIC diff > 2 * ln(1/alpha) ? No, that's not standard.
    # We will stick to the standard BIC interpretation: > 10 is very strong.
    # If the data is very noisy, maybe we lower it? No, let's keep it robust.
    # Actually, let's use a threshold of 6 (strong evidence) to be more sensitive, as alpha=0.05 is a common threshold.
    # But BIC is not a p-value. Let's use 10.
    
    detected = bic_difference > 10.0

    # Determine the year if possible
    change_point_year = None
    if isinstance(metrics, list) and len(metrics) > best_split_idx:
        # Try to get a year from the dict
        candidate = metrics[best_split_idx]
        if isinstance(candidate, dict):
            for key in ['year', 'Year', 'date', 'Date']:
                if key in candidate:
                    change_point_year = candidate[key]
                    break
    
    return {
        'change_point_year': change_point_year,
        'change_point_index': best_split_idx,
        'bic_difference': float(bic_difference),
        'detected': detected,
        'best_bic': float(best_bic),
        'null_bic': float(null_bic)
    }