"""
Statistical analysis module for the self-improving LLM pipeline.

Implements:
- Paired bootstrap testing (α=0.05 strict) for comparing baseline vs. modified model performance.
- Exponential decay curve fitting to detect performance plateaus or degradation over cycles.
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os
from config import get_config

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Exponential decay function: y = a * exp(-b * x) + c
    
    Args:
        x: Array of x-values (e.g., cycle numbers)
        a: Amplitude of decay
        b: Decay rate
        c: Asymptote (plateau value)
    
    Returns:
        y: Fitted values
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(x: np.ndarray, y: np.ndarray) -> Optional[Dict[str, float]]:
    """
    Fit an exponential decay model to the data.
    
    Args:
        x: Array of cycle numbers (independent variable)
        y: Array of performance metrics (dependent variable)
    
    Returns:
        Dictionary with fitted parameters (a, b, c) and R² score, or None if fitting fails.
    """
    if len(x) < 3:
        # Not enough data points for reliable fitting
        return None
    
    try:
        # Provide initial guesses to improve convergence
        # a: initial drop, b: decay rate, c: final plateau
        initial_guess = [y[0] - y[-1], 0.1, y[-1]]
        
        # Bounds: a > 0, b > 0, c can be anything
        bounds = ([0, 0, -np.inf], [np.inf, np.inf, np.inf])
        
        popt, pcov = curve_fit(
            exponential_decay, 
            x, 
            y, 
            p0=initial_guess, 
            bounds=bounds,
            maxfev=5000  # Increase max function evaluations
        )
        
        a, b, c = popt
        
        # Calculate R² score
        y_pred = exponential_decay(x, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "a": float(a),
            "b": float(b),
            "c": float(c),
            "r_squared": float(r_squared)
        }
    except Exception as e:
        # Fitting failed, return None
        return None

def detect_plateau_or_degradation(
    trajectory: List[Dict[str, Any]], 
    metric_key: str = "gsm8k_accuracy"
) -> Dict[str, Any]:
    """
    Detect plateau or degradation cycles from trajectory data using exponential decay fitting.
    
    Args:
        trajectory: List of trajectory entries (each with cycle_number and metrics)
        metric_key: Key in the trajectory entry to use for performance metric
    
    Returns:
        Dictionary with plateau_cycle and degradation_cycle indices (or None if not detected).
    """
    if len(trajectory) < 2:
        return {"plateau_cycle": None, "degradation_cycle": None}
    
    # Extract cycle numbers and metric values
    cycles = np.array([entry["cycle_number"] for entry in trajectory])
    metrics = np.array([entry.get(metric_key, 0.0) for entry in trajectory])
    
    # Fit exponential decay
    fit_params = fit_exponential_decay(cycles, metrics)
    
    if fit_params is None:
        # Fitting failed, fall back to simple heuristic
        # Plateau: last 3 cycles have < 1% change
        if len(metrics) >= 3:
            recent = metrics[-3:]
            max_change = np.max(recent) - np.min(recent)
            if max_change < 0.01 * np.mean(recent):
                plateau_cycle = int(cycles[-3])
            else:
                plateau_cycle = None
        else:
            plateau_cycle = None
        
        # Degradation: last cycle is < 95% of baseline
        baseline = metrics[0]
        if metrics[-1] < 0.95 * baseline:
            degradation_cycle = int(cycles[-1])
        else:
            degradation_cycle = None
        
        return {
            "plateau_cycle": plateau_cycle,
            "degradation_cycle": degradation_cycle,
            "fit_failed": True,
            "method": "heuristic"
        }
    
    # Use fitted curve to detect plateau and degradation
    a, b, c = fit_params["a"], fit_params["b"], fit_params["c"]
    
    # Plateau detection: when the derivative becomes negligible
    # Derivative of exponential decay: dy/dx = -a * b * exp(-b * x)
    # We consider plateau when |dy/dx| < 0.001 (arbitrary threshold)
    # Solve for x: exp(-b * x) < 0.001 / (a * b)
    # -b * x < ln(0.001 / (a * b))
    # x > -ln(0.001 / (a * b)) / b
    
    if a * b > 0:
        threshold = 0.001 / (a * b)
        if threshold > 0:
            plateau_x = -np.log(threshold) / b
            plateau_cycle = int(np.ceil(plateau_x))
            # Clamp to valid range
            plateau_cycle = max(0, min(plateau_cycle, int(cycles[-1])))
        else:
            plateau_cycle = int(cycles[-1])
    else:
        plateau_cycle = None
    
    # Degradation detection: when metric drops below 95% of baseline
    baseline = metrics[0]
    degradation_threshold = 0.95 * baseline
    
    degradation_cycle = None
    for i, (cycle, metric) in enumerate(zip(cycles, metrics)):
        if metric < degradation_threshold:
            degradation_cycle = int(cycle)
            break
    
    return {
        "plateau_cycle": plateau_cycle,
        "degradation_cycle": degradation_cycle,
        "fit_params": fit_params,
        "fit_failed": False,
        "method": "exponential_decay"
    }

def paired_bootstrap_test(
    baseline_scores: List[float], 
    modified_scores: List[float], 
    n_iterations: int = 1000, 
    alpha: float = 0.05, 
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform a paired bootstrap test to compare baseline vs. modified model performance.
    
    This test assesses whether the difference in means between two related samples
    (baseline and modified) is statistically significant.
    
    Args:
        baseline_scores: List of baseline performance scores (e.g., from multiple runs)
        modified_scores: List of modified model performance scores (same length as baseline)
        n_iterations: Number of bootstrap iterations
        alpha: Significance level (default 0.05)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary with p-value, confidence interval, and test conclusion.
    """
    if len(baseline_scores) != len(modified_scores):
        raise ValueError("baseline_scores and modified_scores must have the same length")
    
    if len(baseline_scores) == 0:
        raise ValueError("Input lists cannot be empty")
    
    if seed is not None:
        np.random.seed(seed)
    
    n = len(baseline_scores)
    differences = np.array(modified_scores) - np.array(baseline_scores)
    
    # Bootstrap resampling of differences
    bootstrap_means = []
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        resampled_diff = differences[indices]
        bootstrap_means.append(np.mean(resampled_diff))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate p-value (two-tailed test)
    observed_mean_diff = np.mean(differences)
    
    # Count how many bootstrap means are as extreme or more extreme than observed
    # Two-tailed: consider both tails
    extreme_count = np.sum(np.abs(bootstrap_means) >= np.abs(observed_mean_diff))
    p_value = extreme_count / n_iterations
    
    # Calculate 95% confidence interval
    confidence_level = 1 - alpha
    ci_lower = np.percentile(bootstrap_means, (1 - confidence_level) / 2 * 100)
    ci_upper = np.percentile(bootstrap_means, (1 + confidence_level) / 2 * 100)
    
    # Determine significance
    is_significant = p_value < alpha
    
    return {
        "p_value": float(p_value),
        "confidence_interval": [float(ci_lower), float(ci_upper)],
        "observed_mean_difference": float(observed_mean_diff),
        "is_significant": is_significant,
        "alpha": alpha,
        "n_iterations": n_iterations,
        "n_samples": n
    }

def save_decay_fit_results(
    results: Dict[str, Any], 
    output_path: Optional[str] = None
) -> str:
    """
    Save exponential decay fit results to a JSON file.
    
    Args:
        results: Dictionary containing decay fit results
        output_path: Path to output file (default: results/decay_summary.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = os.path.join(config.results_dir, "decay_summary.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return output_path

def save_bootstrap_results(
    results: Dict[str, Any], 
    output_path: Optional[str] = None
) -> str:
    """
    Save bootstrap test results to a JSON file.
    
    Args:
        results: Dictionary containing bootstrap test results
        output_path: Path to output file (default: results/bootstrap_results.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = os.path.join(config.results_dir, "bootstrap_results.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return output_path