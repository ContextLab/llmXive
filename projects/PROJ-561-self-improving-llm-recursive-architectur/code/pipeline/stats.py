import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os
import logging
from config import get_config

logger = logging.getLogger(__name__)

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Exponential decay function: y = a * exp(-b * x) + c
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Fit an exponential decay model to the data.
    Returns dictionary with fitted parameters and goodness of fit.
    """
    try:
        popt, pcov = curve_fit(exponential_decay, x, y, p0=[y[0], 1.0, y[-1]])
        a, b, c = popt
        
        # Calculate R-squared
        y_pred = exponential_decay(x, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'a': float(a),
            'b': float(b),
            'c': float(c),
            'r_squared': float(r_squared)
        }
    except Exception as e:
        logger.warning(f"Exponential decay fit failed: {e}")
        return {'a': 0.0, 'b': 0.0, 'c': 0.0, 'r_squared': 0.0}

def detect_plateau_or_degradation(metrics: List[float], threshold: float = 0.01) -> str:
    """
    Detect if the metrics show a plateau or degradation.
    Returns 'plateau', 'degradation', or 'improving'.
    """
    if len(metrics) < 2:
        return 'improving'
    
    # Check for recent degradation
    recent_change = metrics[-1] - metrics[-2]
    if recent_change < -threshold:
        return 'degradation'
    
    # Check for plateau (small changes)
    if abs(recent_change) < threshold:
        return 'plateau'
    
    return 'improving'

def paired_bootstrap_test(
    baseline: List[float], 
    post_mod: List[float], 
    n_resamples: int = 1000, 
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired bootstrap test to compare baseline and post-modification metrics.
    Returns p-value and significance determination.
    """
    if len(baseline) != len(post_mod):
        raise ValueError("Baseline and post_mod must have the same length for paired test")
    
    n_pairs = len(baseline)
    diff_original = np.mean(post_mod) - np.mean(baseline)
    
    # Bootstrap resampling
    boot_diffs = []
    for _ in range(n_resamples):
        indices = np.random.choice(n_pairs, size=n_pairs, replace=True)
        boot_baseline = np.array(baseline)[indices]
        boot_post_mod = np.array(post_mod)[indices]
        diff = np.mean(boot_post_mod) - np.mean(boot_baseline)
        boot_diffs.append(diff)
    
    boot_diffs = np.array(boot_diffs)
    
    # Calculate p-value (two-tailed)
    p_value = 2 * min(
        np.sum(boot_diffs >= diff_original) / n_resamples,
        np.sum(boot_diffs <= diff_original) / n_resamples
    )
    
    is_significant = p_value < alpha
    
    # Determine significance
    is_significant = p_value < alpha
    
    return {
        'p_value': float(p_value),
        'is_significant': bool(is_significant),
        'alpha': alpha,
        'n_resamples': n_resamples,
        'original_difference': float(diff_original),
        'bootstrap_mean': float(np.mean(boot_diffs)),
        'bootstrap_std': float(np.std(boot_diffs))
    }

def linear_regression_trend(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Perform linear regression to analyze trend in performance trajectory.
    Returns slope, intercept, r_squared, and trend direction.
    """
    if len(x) < 2:
        return {
            'slope': 0.0,
            'intercept': y[0] if len(y) > 0 else 0.0,
            'r_squared': 0.0,
            'trend_direction': 'flat'
        }
    
    # Linear regression
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        slope = 0.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    intercept = (sum_y - slope * sum_x) / n
    
    # R-squared calculation
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
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

def save_decay_fit_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save exponential decay fit results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Decay fit results saved to {output_path}")

def save_bootstrap_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save bootstrap test results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Bootstrap results saved to {output_path}")

def get_bootstrap_resamples() -> int:
    """
    Get the number of bootstrap resamples from config.
    """
    config = get_config()
    return getattr(config, 'bootstrap_resamples', 1000)
