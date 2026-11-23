import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os
from config import get_config

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Model function for exponential decay with offset: f(x) = a * exp(-b * x) + c
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(x: np.ndarray, y: np.ndarray) -> Optional[Dict[str, float]]:
    """
    Fits the exponential decay model to the data.
    Returns a dict with fitted parameters if successful, None otherwise.
    """
    try:
        # Initial guesses: a=range(y), b=1.0, c=min(y)
        p0 = [y[0] - y[-1], 0.1, y[-1]]
        bounds = ([0, 0, -np.inf], [np.inf, np.inf, np.inf])
        
        popt, _ = curve_fit(exponential_decay, x, y, p0=p0, bounds=bounds, maxfev=2000)
        return {
            'a': float(popt[0]),
            'b': float(popt[1]),
            'c': float(popt[2])
        }
    except Exception:
        return None

def detect_plateau_or_degradation(y: np.ndarray, threshold: float = 0.05) -> Dict[str, Any]:
    """
    Detects if the performance has plateaued or degraded.
    Compares the last N points to the overall trend.
    """
    if len(y) < 3:
        return {'plateau': False, 'degradation': False, 'reason': 'Insufficient data'}
    
    # Simple check: is the last value significantly lower than the max?
    max_val = np.max(y)
    last_val = y[-1]
    
    degradation = (max_val - last_val) / max_val > threshold if max_val > 0 else False
    
    # Check for plateau: variance of last 3 points is very low relative to mean
    if len(y) >= 3:
        recent = y[-3:]
        mean_recent = np.mean(recent)
        std_recent = np.std(recent)
        plateau = (std_recent / mean_recent < 0.01) if mean_recent > 0 else False
    else:
        plateau = False
        
    return {
        'plateau': bool(plateau),
        'degradation': bool(degradation),
        'max_value': float(max_val),
        'last_value': float(last_val)
    }

def paired_bootstrap_test(
    baseline_scores: List[float], 
    new_scores: List[float], 
    num_resamples: int = 1000, 
    seed: int = 42
) -> Dict[str, Any]:
    """
    Performs a paired bootstrap test to compare two sets of scores.
    Returns statistical significance and effect size.
    """
    if len(baseline_scores) != len(new_scores):
        raise ValueError("Baseline and new scores must have the same length for paired test.")
    
    np.random.seed(seed)
    n = len(baseline_scores)
    diff_mean = np.mean(new_scores) - np.mean(baseline_scores)
    
    bootstrap_diffs = []
    for _ in range(num_resamples):
        indices = np.random.choice(n, n, replace=True)
        b_sample = [baseline_scores[i] for i in indices]
        n_sample = [new_scores[i] for i in indices]
        bootstrap_diffs.append(np.mean(n_sample) - np.mean(b_sample))
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    p_value = (np.sum(np.abs(bootstrap_diffs) >= np.abs(diff_mean)) + 1) / (num_resamples + 1)
    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)
    
    return {
        'observed_difference': float(diff_mean),
        'p_value': float(p_value),
        'confidence_interval_95': [float(ci_lower), float(ci_upper)],
        'significant_at_0.05': bool(p_value < 0.05),
        'num_resamples': num_resamples
    }

def linear_regression_trend(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Performs a simple linear regression y = mx + c.
    Returns slope, intercept, and R-squared.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x and y must have the same length >= 2.")
    
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        slope = 0.0
        intercept = float(np.mean(y))
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
    
    # R-squared calculation
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared)
    }

def get_bootstrap_resamples() -> int:
    """
    Reads NUM_RESAMPLES from config.py.
    """
    config = get_config()
    # Default to 1000 if not explicitly set in Hyperparameters or SafetyConstraints
    if hasattr(config, 'hyperparameters') and hasattr(config.hyperparameters, 'num_resamples'):
        return config.hyperparameters.num_resamples
    # Fallback to a reasonable default if not in config
    return 1000

def save_bootstrap_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Saves bootstrap test results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def save_decay_fit_results(results: Dict[str, float], output_path: str) -> None:
    """
    Saves exponential decay fit results to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_bootstrap_and_regression(
    baseline_scores: List[float],
    new_scores: List[float],
    cycle_indices: np.ndarray,
    performance_history: List[float]
) -> Dict[str, Any]:
    """
    Main entry point for statistical analysis.
    Runs paired bootstrap test and linear regression trend analysis.
    Reads NUM_RESAMPLES from config.py.
    """
    config = get_config()
    num_resamples = get_bootstrap_resamples()
    
    # Paired Bootstrap Test
    bootstrap_results = paired_bootstrap_test(
        baseline_scores, 
        new_scores, 
        num_resamples=num_resamples,
        seed=getattr(config, 'seed', 42)
    )
    
    # Linear Regression Trend
    regression_results = linear_regression_trend(cycle_indices, np.array(performance_history))
    
    # Plateau/Degradation Check
    plateau_results = detect_plateau_or_degradation(np.array(performance_history))
    
    return {
        'bootstrap_test': bootstrap_results,
        'regression_trend': regression_results,
        'plateau_analysis': plateau_results,
        'num_resamples_used': num_resamples
    }
