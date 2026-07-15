"""
Statistical analysis utilities for the self-improving LLM pipeline.
Implements paired bootstrap testing and exponential decay curve fitting.
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Exponential decay model: y = a * exp(-b * x) + c
    
    Args:
        x: Independent variable (cycle number)
        a: Amplitude (initial value - asymptote)
        b: Decay rate
        c: Asymptote (limiting value)
        
    Returns:
        Fitted values
    """
    return a * np.exp(-b * x) + c


def paired_bootstrap_test(
    baseline_scores: List[float],
    modified_scores: List[float],
    alpha: float = 0.05,
    n_iterations: int = 10000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform paired bootstrap hypothesis test to determine if modified scores
    are significantly different from baseline scores.
    
    Uses a strict alpha level (default 0.05) and performs a two-tailed test.
    The test is paired, meaning we resample indices and compute the difference
    for each pair.
    
    Args:
        baseline_scores: List of baseline performance scores (e.g., accuracy)
        modified_scores: List of modified performance scores (same length as baseline)
        alpha: Significance level (default 0.05)
        n_iterations: Number of bootstrap iterations (default 10000)
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing:
            - 'mean_diff': Mean difference (modified - baseline)
            - 'p_value': Two-tailed p-value from bootstrap test
            - 'is_significant': Boolean indicating if p < alpha
            - 'confidence_interval': 95% confidence interval for the mean difference
            - 'bootstrap_distribution': Array of bootstrap mean differences
    """
    if seed is not None:
        np.random.seed(seed)
        
    if len(baseline_scores) != len(modified_scores):
        raise ValueError("Baseline and modified scores must have the same length")
        
    if len(baseline_scores) == 0:
        raise ValueError("Score lists cannot be empty")
        
    n_pairs = len(baseline_scores)
    baseline_arr = np.array(baseline_scores)
    modified_arr = np.array(modified_scores)
    
    # Compute observed mean difference
    observed_diff = np.mean(modified_arr - baseline_arr)
    
    # Bootstrap resampling
    bootstrap_diffs = np.zeros(n_iterations)
    for i in range(n_iterations):
        # Resample indices with replacement
        indices = np.random.choice(n_pairs, size=n_pairs, replace=True)
        # Compute mean difference for this bootstrap sample
        bootstrap_diffs[i] = np.mean(modified_arr[indices] - baseline_arr[indices])
    
    # Calculate p-value (two-tailed)
    # Count how many bootstrap diffs are as extreme or more extreme than observed
    # For two-tailed test, we consider both tails
    abs_observed = abs(observed_diff)
    abs_bootstrap = np.abs(bootstrap_diffs)
    p_value = np.mean(abs_bootstrap >= abs_observed)
    
    # Calculate 95% confidence interval
    confidence_level = 0.95
    lower_percentile = (1 - confidence_level) / 2 * 100
    upper_percentile = (1 + confidence_level) / 2 * 100
    ci_lower = np.percentile(bootstrap_diffs, lower_percentile)
    ci_upper = np.percentile(bootstrap_diffs, upper_percentile)
    
    return {
        'mean_diff': float(observed_diff),
        'p_value': float(p_value),
        'is_significant': bool(p_value < alpha),
        'confidence_interval': (float(ci_lower), float(ci_upper)),
        'bootstrap_distribution': bootstrap_diffs.tolist()
    }


def fit_exponential_decay(
    x_values: List[float],
    y_values: List[float],
    p0: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """
    Fit an exponential decay model to the data.
    
    Model: y = a * exp(-b * x) + c
    
    Args:
        x_values: Independent variable values (e.g., cycle numbers)
        y_values: Dependent variable values (e.g., performance metrics)
        p0: Initial guess for parameters (a, b, c). If None, uses heuristics.
            
    Returns:
        Dictionary containing:
            - 'params': Fitted parameters (a, b, c)
            - 'r_squared': Coefficient of determination
            - 'success': Boolean indicating if fitting succeeded
            - 'message': Status message
            - 'predicted_values': Predicted y values for given x values
    """
    x_arr = np.array(x_values)
    y_arr = np.array(y_values)
    
    if len(x_arr) != len(y_arr):
        raise ValueError("x_values and y_values must have the same length")
        
    if len(x_arr) < 3:
        raise ValueError("At least 3 data points are required for fitting")
        
    # Initial parameter guesses if not provided
    if p0 is None:
        # Heuristic initial guesses
        a_init = y_arr[0] - y_arr[-1]  # Approximate amplitude
        b_init = 0.1  # Default decay rate
        c_init = y_arr[-1]  # Approximate asymptote
        p0 = (a_init, b_init, c_init)
        
    try:
        # Fit the model
        popt, pcov = curve_fit(
            exponential_decay, 
            x_arr, 
            y_arr, 
            p0=p0, 
            maxfev=10000,
            bounds=([0, 0, -np.inf], [np.inf, np.inf, np.inf])
        )
        
        a, b, c = popt
        
        # Calculate R-squared
        y_pred = exponential_decay(x_arr, *popt)
        ss_res = np.sum((y_arr - y_pred) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'params': {'a': float(a), 'b': float(b), 'c': float(c)},
            'r_squared': float(r_squared),
            'success': True,
            'message': 'Fitting successful',
            'predicted_values': y_pred.tolist()
        }
        
    except Exception as e:
        return {
            'params': None,
            'r_squared': None,
            'success': False,
            'message': f'Fitting failed: {str(e)}',
            'predicted_values': None
        }


def detect_plateau_or_degradation(
    x_values: List[float],
    y_values: List[float],
    window_size: int = 3,
    threshold: float = 0.01
) -> Dict[str, Any]:
    """
    Detect plateau or degradation in a time series using the fitted exponential decay model.
    
    A plateau is detected when the slope of the fitted curve becomes negligible.
    A degradation is detected when the metric decreases significantly over a window.
    
    Args:
        x_values: Cycle numbers
        y_values: Performance metrics
        window_size: Number of points to consider for local trend
        threshold: Slope threshold for plateau detection (as fraction of initial value)
            
    Returns:
        Dictionary containing:
            - 'plateau_cycle': Cycle number where plateau was detected (None if not found)
            - 'degradation_cycle': Cycle number where degradation started (None if not found)
            - 'trend': Overall trend ('improving', 'plateau', 'degrading')
    """
    if len(x_values) != len(y_values) or len(x_values) < window_size:
        return {
            'plateau_cycle': None,
            'degradation_cycle': None,
            'trend': 'insufficient_data'
        }
        
    # Fit exponential decay
    fit_result = fit_exponential_decay(x_values, y_values)
    
    if not fit_result['success']:
        return {
            'plateau_cycle': None,
            'degradation_cycle': None,
            'trend': 'fit_failed'
        }
        
    params = fit_result['params']
    a, b, c = params['a'], params['b'], params['c']
    
    # Calculate derivative of the fitted curve: dy/dx = -a*b*exp(-b*x)
    # Find where the absolute slope becomes negligible
    plateau_cycle = None
    for i, x in enumerate(x_values):
        slope = -a * b * np.exp(-b * x)
        # Normalize slope by initial value (a + c)
        normalized_slope = abs(slope) / (abs(a) + abs(c) + 1e-8)
        if normalized_slope < threshold:
            plateau_cycle = int(x)
            break
    
    # Check for degradation: look for significant drop in recent window
    degradation_cycle = None
    if len(x_values) >= window_size:
        recent_y = y_values[-window_size:]
        recent_x = x_values[-window_size:]
        
        # Simple linear regression on recent window to estimate trend
        if len(recent_x) > 1:
            coeffs = np.polyfit(recent_x, recent_y, 1)
            slope_recent = coeffs[0]
            
            # If slope is significantly negative, consider it degradation
            initial_val = y_values[0]
            if slope_recent < -threshold * initial_val:
                # Find the first point where the drop becomes significant
                for i in range(len(x_values) - window_size, len(x_values)):
                    window_start = max(0, i - window_size + 1)
                    window_y = y_values[window_start:i+1]
                    if len(window_y) > 1:
                        local_slope = (window_y[-1] - window_y[0]) / (i - window_start + 1e-8)
                        if local_slope < -threshold * initial_val:
                            degradation_cycle = int(x_values[i])
                            break
    
    # Determine overall trend
    if degradation_cycle is not None:
        trend = 'degrading'
    elif plateau_cycle is not None:
        trend = 'plateau'
    else:
        # Check overall improvement
        if y_values[-1] > y_values[0]:
            trend = 'improving'
        else:
            trend = 'degrading'
            
    return {
        'plateau_cycle': plateau_cycle,
        'degradation_cycle': degradation_cycle,
        'trend': trend
    }


def save_bootstrap_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save bootstrap test results to a JSON file.
    
    Args:
        results: Dictionary containing bootstrap test results
        output_path: Path to save the JSON file
    """
    # Remove numpy arrays before saving
    clean_results = {}
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            clean_results[key] = value.tolist()
        else:
            clean_results[key] = value
            
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)


def save_decay_fit_results(
    fit_result: Dict[str, Any],
    x_values: List[float],
    y_values: List[float],
    output_path: str
) -> None:
    """
    Save exponential decay fitting results to a JSON file.
    
    Args:
        fit_result: Dictionary containing fitting results
        x_values: Original x values
        y_values: Original y values
        output_path: Path to save the JSON file
    """
    output_data = {
        'original_data': {
            'x': x_values,
            'y': y_values
        },
        'fit_results': fit_result
    }
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)