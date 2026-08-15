import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os
from config import get_config

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Exponential decay model: y = a * exp(-b * x) + c
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """
    Fit an exponential decay model to the data.
    Returns (a, b, c) parameters.
    """
    if len(x) < 3:
        raise ValueError("Need at least 3 data points to fit exponential decay.")
    
    try:
        popt, _ = curve_fit(exponential_decay, x, y, p0=[y[0], 0.1, y[-1]])
        return float(popt[0]), float(popt[1]), float(popt[2])
    except RuntimeError:
        raise RuntimeError("Failed to fit exponential decay model.")

def detect_plateau_or_degradation(params: Tuple[float, float, float], threshold: float = 0.01) -> str:
    """
    Detect if the fitted exponential decay has plateaued or is degrading.
    params: (a, b, c) from exponential decay fit.
    Returns: 'plateau', 'degradation', or 'improving'.
    """
    a, b, c = params
    if b < threshold:
        return 'plateau'
    elif a < 0:
        return 'degradation'
    else:
        return 'improving'

def paired_bootstrap_test(
    baseline_scores: List[float],
    modified_scores: List[float],
    alpha: float = 0.05,
    resamples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform a paired bootstrap test to compare baseline and modified scores.
    
    Args:
        baseline_scores: List of scores from the baseline model.
        modified_scores: List of scores from the modified model.
        alpha: Significance level (default 0.05).
        resamples: Number of bootstrap resamples (defaults to config value).
    
    Returns:
        Dictionary containing p-value, confidence interval, and test result.
    """
    if len(baseline_scores) != len(modified_scores):
        raise ValueError("Baseline and modified scores must have the same length for paired test.")
    
    if len(baseline_scores) == 0:
        raise ValueError("Scores lists cannot be empty.")
    
    if resamples is None:
        config = get_config()
        resamples = config.hyperparameters.bootstrap_resamples
    
    baseline_arr = np.array(baseline_scores)
    modified_arr = np.array(modified_scores)
    
    # Calculate observed difference (modified - baseline)
    observed_diff = np.mean(modified_arr) - np.mean(baseline_arr)
    
    # Bootstrap resampling
    np.random.seed(42)  # For reproducibility
    bootstrap_diffs = []
    n = len(baseline_arr)
    
    for _ in range(resamples):
        indices = np.random.choice(n, size=n, replace=True)
        resampled_baseline = baseline_arr[indices]
        resampled_modified = modified_arr[indices]
        diff = np.mean(resampled_modified) - np.mean(resampled_baseline)
        bootstrap_diffs.append(diff)
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Calculate p-value (two-tailed)
    p_value = 2 * min(
        np.mean(bootstrap_diffs >= observed_diff),
        np.mean(bootstrap_diffs <= observed_diff)
    )
    
    # Calculate 95% confidence interval
    ci_lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))
    
    # Determine significance
    is_significant = p_value < alpha
    
    return {
        'observed_difference': float(observed_diff),
        'p_value': float(p_value),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'is_significant': bool(is_significant),
        'alpha': float(alpha),
        'resamples': int(resamples)
    }

def linear_regression_trend(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Perform linear regression to analyze trend in performance over cycles.
    
    Args:
        x: Independent variable (e.g., cycle numbers).
        y: Dependent variable (e.g., performance metric).
    
    Returns:
        Dictionary containing slope, intercept, r_squared, and trend direction.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 data points for linear regression.")
    
    n = len(x)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    # Calculate slope and intercept
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        raise ValueError("Cannot compute regression: x values are constant.")
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    
    if ss_tot == 0:
        r_squared = 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    # Determine trend direction
    if slope > 0.001:
        trend_direction = 'improving'
    elif slope < -0.001:
        trend_direction = 'declining'
    else:
        trend_direction = 'flat'
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared),
        'trend_direction': trend_direction
    }

def save_bootstrap_results(results: Dict[str, Any], filepath: str) -> None:
    """
    Save bootstrap test results to a JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

def save_decay_fit_results(params: Tuple[float, float, float], trend: str, filepath: str) -> None:
    """
    Save exponential decay fit results to a JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    data = {
        'a': params[0],
        'b': params[1],
        'c': params[2],
        'trend': trend
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
