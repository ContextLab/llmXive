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
    
    Args:
        x: Array of x values (cycle numbers)
        a: Amplitude (initial value - asymptote)
        b: Decay rate
        c: Asymptote (plateau value)
    
    Returns:
        Predicted y values
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(
    cycles: List[int], 
    values: List[float]
) -> Optional[Dict[str, Any]]:
    """
    Fit an exponential decay model to performance data across cycles.
    
    Args:
        cycles: List of cycle numbers (x-values)
        values: List of performance metrics (y-values)
    
    Returns:
        Dictionary with fit parameters (a, b, c), R² score, and fitted curve points,
        or None if fitting fails (e.g., insufficient data).
    """
    if len(cycles) < 3:
        return None
    
    x = np.array(cycles, dtype=float)
    y = np.array(values, dtype=float)
    
    # Normalize x to start at 0 for better numerical stability
    x_normalized = x - x[0]
    
    # Initial guesses: a = y[0] - y[-1], b = 0.1, c = y[-1]
    try:
        p0 = [y[0] - y[-1], 0.1, y[-1]]
        # Ensure positive decay rate
        p0[0] = abs(p0[0]) if abs(p0[0]) > 1e-6 else 1.0
        p0[1] = abs(p0[1]) if p0[1] > 1e-6 else 0.1
        p0[2] = y[-1]
        
        popt, pcov = curve_fit(
            exponential_decay, 
            x_normalized, 
            y, 
            p0=p0,
            bounds=([0, 1e-6, -np.inf], [np.inf, 10, np.inf]),
            maxfev=5000
        )
        
        a, b, c = popt
        
        # Calculate R² score
        y_pred = exponential_decay(x_normalized, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Generate fitted curve points for plotting
        x_fit = np.linspace(x_normalized[0], x_normalized[-1], 100)
        y_fit = exponential_decay(x_fit, *popt)
        
        return {
            "parameters": {
                "a": float(a),
                "b": float(b),
                "c": float(c)
            },
            "r_squared": float(r_squared),
            "fitted_curve": {
                "x": x_fit.tolist(),
                "y": y_fit.tolist()
            },
            "original_data": {
                "x": x.tolist(),
                "y": y.tolist()
            }
        }
    except Exception:
        # Fitting failed (e.g., numerical issues, insufficient data variation)
        return None

def detect_plateau_or_degradation(
    cycles: List[int],
    values: List[float],
    threshold_percent: float = 5.0
) -> Dict[str, Any]:
    """
    Detect the cycle where performance plateaus or begins to degrade.
    
    A plateau is identified when the improvement between consecutive cycles
    drops below a threshold. Degradation is identified when performance
    drops by more than the threshold percentage from the baseline (first cycle).
    
    Args:
        cycles: List of cycle numbers
        values: List of performance metrics
        threshold_percent: Percentage threshold for degradation detection (default 5%)
    
    Returns:
        Dictionary with:
            - plateau_cycle: Cycle number where plateau was detected (or None)
            - degradation_cycle: Cycle number where degradation was detected (or None)
            - is_plateau: Boolean indicating if a plateau was found
            - is_degradation: Boolean indicating if degradation was found
            - baseline_value: Value at cycle 0
            - max_value: Maximum value observed
            - final_value: Value at the last cycle
    """
    if len(values) < 2:
        return {
            "plateau_cycle": None,
            "degradation_cycle": None,
            "is_plateau": False,
            "is_degradation": False,
            "baseline_value": values[0] if values else None,
            "max_value": max(values) if values else None,
            "final_value": values[-1] if values else None
        }
    
    baseline_value = values[0]
    max_value = max(values)
    final_value = values[-1]
    
    plateau_cycle = None
    degradation_cycle = None
    is_plateau = False
    is_degradation = False
    
    # Check for degradation: performance drops >= threshold_percent from baseline
    for i, (cycle, value) in enumerate(zip(cycles, values)):
        if i == 0:
            continue
        
        # Calculate percentage change from baseline
        if baseline_value != 0:
            pct_change = ((value - baseline_value) / abs(baseline_value)) * 100
        else:
            pct_change = 0
        
        if pct_change <= -threshold_percent:
            degradation_cycle = cycle
            is_degradation = True
            break
    
    # Check for plateau: improvement between consecutive cycles drops significantly
    # We define plateau as when the gain is less than 10% of the previous gain
    # or when the absolute gain is very small
    if len(values) >= 3:
        gains = []
        for i in range(1, len(values)):
            gain = values[i] - values[i-1]
            gains.append(gain)
        
        # Look for the first point where gains diminish significantly
        for i in range(1, len(gains)):
            prev_gain = gains[i-1]
            curr_gain = gains[i]
            
            # If previous gain was positive and current gain is much smaller
            if prev_gain > 0.001:  # Avoid division by zero
                gain_ratio = curr_gain / prev_gain
                
                # Plateau detected if gain drops to less than 10% of previous gain
                # or if the absolute gain is very small (less than 0.1% of baseline)
                if gain_ratio < 0.1 or abs(curr_gain) < (0.001 * abs(baseline_value)):
                    plateau_cycle = cycles[i+1]  # Cycle corresponding to current gain
                    is_plateau = True
                    break
            elif prev_gain <= 0 and curr_gain <= 0:
                # Both gains are non-positive, likely a plateau or degradation
                if plateau_cycle is None:
                    plateau_cycle = cycles[i+1]
                    is_plateau = True
                    break
    
    return {
        "plateau_cycle": plateau_cycle,
        "degradation_cycle": degradation_cycle,
        "is_plateau": is_plateau,
        "is_degradation": is_degradation,
        "baseline_value": float(baseline_value),
        "max_value": float(max_value),
        "final_value": float(final_value)
    }

def paired_bootstrap_test(
    baseline_values: List[float],
    modified_values: List[float],
    n_iterations: int = 1000,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform paired bootstrap test to compare two sets of values.
    
    Args:
        baseline_values: List of baseline performance values
        modified_values: List of modified performance values
        n_iterations: Number of bootstrap iterations
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with:
            - mean_diff: Mean difference (modified - baseline)
            - ci_lower: Lower bound of 95% confidence interval
            - ci_upper: Upper bound of 95% confidence interval
            - p_value: Two-tailed p-value
            - is_significant: Boolean indicating if difference is significant
    """
    if len(baseline_values) != len(modified_values) or len(baseline_values) == 0:
        return {
            "mean_diff": None,
            "ci_lower": None,
            "ci_upper": None,
            "p_value": None,
            "is_significant": False
        }
    
    baseline = np.array(baseline_values)
    modified = np.array(modified_values)
    
    # Calculate observed mean difference
    observed_diff = np.mean(modified - baseline)
    
    # Bootstrap resampling
    n = len(baseline)
    bootstrap_diffs = []
    
    for _ in range(n_iterations):
        indices = np.random.choice(n, size=n, replace=True)
        resampled_baseline = baseline[indices]
        resampled_modified = modified[indices]
        bootstrap_diff = np.mean(resampled_modified - resampled_baseline)
        bootstrap_diffs.append(bootstrap_diff)
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Calculate confidence interval
    ci_lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))
    
    # Calculate p-value (two-tailed)
    # Count how many bootstrap samples have absolute difference >= observed absolute difference
    abs_observed = abs(observed_diff)
    abs_bootstrap = np.abs(bootstrap_diffs)
    p_value = np.mean(abs_bootstrap >= abs_observed)
    
    is_significant = (ci_lower > 0) or (ci_upper < 0)
    
    return {
        "mean_diff": float(observed_diff),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "p_value": float(p_value),
        "is_significant": is_significant
    }

def save_decay_fit_results(
    fit_results: Optional[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save exponential decay fit results to a JSON file.
    
    Args:
        fit_results: Results from fit_exponential_decay() or None
        output_path: Optional path to save results. If None, uses config path.
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = os.path.join(config.results_dir, "decay_fit_results.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        "fit_successful": fit_results is not None,
        "results": fit_results,
        "timestamp": str(np.datetime64('now'))
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_path

def save_bootstrap_results(
    bootstrap_results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save bootstrap test results to a JSON file.
    
    Args:
        bootstrap_results: Results from paired_bootstrap_test()
        output_path: Optional path to save results. If None, uses config path.
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = os.path.join(config.results_dir, "bootstrap_results.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        "test_results": bootstrap_results,
        "timestamp": str(np.datetime64('now'))
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_path