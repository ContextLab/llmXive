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
from config import get_config

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Exponential decay model: y = a * exp(-b * x) + c
    
    Args:
        x: Independent variable (e.g., cycle number)
        a: Amplitude of decay
        b: Decay rate
        c: Asymptotic value (plateau)
    
    Returns:
        y: Modeled values
    """
    return a * np.exp(-b * x) + c

def fit_exponential_decay(
    x: np.ndarray,
    y: np.ndarray,
    p0: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """
    Fit an exponential decay model to data.
    
    Args:
        x: Independent variable array (e.g., cycle numbers)
        y: Dependent variable array (e.g., performance metrics)
        p0: Initial guess for parameters (a, b, c). If None, uses defaults.
    
    Returns:
        Dictionary containing:
            - params: Fitted parameters (a, b, c)
            - success: Boolean indicating if fitting succeeded
            - message: Status message
            - r_squared: Coefficient of determination
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    
    if len(x) < 3:
        return {
            "params": None,
            "success": False,
            "message": "Insufficient data points for curve fitting (need >= 3)",
            "r_squared": None
        }
    
    if p0 is None:
        # Default initial guesses
        p0 = (y[0] - y[-1], 0.1, y[-1])
    
    try:
        popt, pcov = curve_fit(exponential_decay, x, y, p0=p0, maxfev=5000)
        
        # Calculate R-squared
        y_pred = exponential_decay(x, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            "params": popt.tolist(),
            "success": True,
            "message": "Fit successful",
            "r_squared": float(r_squared)
        }
    except Exception as e:
        return {
            "params": None,
            "success": False,
            "message": f"Fit failed: {str(e)}",
            "r_squared": None
        }

def detect_plateau_or_degradation(
    trajectory_data: List[Dict[str, Any]],
    metric_key: str = "GSM8K",
    degradation_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Analyze trajectory data to detect plateau or degradation cycles.
    
    Args:
        trajectory_data: List of trajectory entries from results/trajectory.json
        metric_key: Key to use for performance metric (default: "GSM8K")
        degradation_threshold: Relative threshold for degradation (default: 5%)
    
    Returns:
        Dictionary containing:
            - plateau_cycle: Cycle number where plateau was detected (or None)
            - degradation_cycle: Cycle number where degradation was detected (or None)
            - plateau_threshold: The metric value at plateau
            - degradation_value: The metric value at degradation
    """
    if not trajectory_data:
        return {
            "plateau_cycle": None,
            "degradation_cycle": None,
            "plateau_threshold": None,
            "degradation_value": None
        }
    
    cycles = []
    values = []
    
    for entry in trajectory_data:
        if metric_key in entry:
            cycles.append(entry.get("cycle_number", len(cycles)))
            values.append(entry[metric_key])
    
    if len(values) < 2:
        return {
            "plateau_cycle": None,
            "degradation_cycle": None,
            "plateau_threshold": None,
            "degradation_value": None
        }
    
    # Detect degradation: if current value drops below (1 - threshold) * baseline
    baseline = values[0]
    degradation_cycle = None
    degradation_value = None
    
    for i, val in enumerate(values):
        if val < baseline * (1 - degradation_threshold):
            degradation_cycle = cycles[i]
            degradation_value = val
            break
    
    # Detect plateau: fit exponential decay and find where change < 1% of asymptotic value
    plateau_cycle = None
    plateau_threshold = None
    
    if len(values) >= 3:
        x_arr = np.array(list(range(len(values))))
        y_arr = np.array(values)
        
        fit_result = fit_exponential_decay(x_arr, y_arr)
        
        if fit_result["success"] and fit_result["params"]:
            a, b, c = fit_result["params"]
            
            # Plateau detected when the derivative is small relative to the asymptotic value
            # dy/dx = -a * b * exp(-b * x)
            # We consider plateau when |dy/dx| < 0.01 * |c| (1% of asymptotic value)
            for i, x_val in enumerate(x_arr):
                derivative = -a * b * np.exp(-b * x_val)
                if abs(derivative) < 0.01 * abs(c) if c != 0 else 0.001:
                    plateau_cycle = cycles[i]
                    plateau_threshold = float(c)
                    break
    
    return {
        "plateau_cycle": plateau_cycle,
        "degradation_cycle": degradation_cycle,
        "plateau_threshold": plateau_threshold,
        "degradation_value": degradation_value
    }

def paired_bootstrap_test(
    baseline_scores: List[float],
    post_mod_scores: List[float],
    alpha: float = 0.05,
    n_iterations: int = 10000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform paired bootstrap test to compare two distributions.
    
    This test assesses whether the post-modification scores are significantly
    different from baseline scores using a paired bootstrap approach.
    
    Args:
        baseline_scores: List of baseline performance scores
        post_mod_scores: List of post-modification performance scores
        alpha: Significance level (default: 0.05)
        n_iterations: Number of bootstrap iterations (default: 10000)
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Dictionary containing:
            - p_value: Calculated p-value
            - significant: Boolean indicating if difference is significant at alpha
            - mean_baseline: Mean of baseline scores
            - mean_post_mod: Mean of post-modification scores
            - mean_diff: Mean difference (post_mod - baseline)
            - ci_lower: Lower bound of 95% confidence interval
            - ci_upper: Upper bound of 95% confidence interval
    """
    if len(baseline_scores) != len(post_mod_scores):
        raise ValueError("baseline_scores and post_mod_scores must have the same length")
    
    if len(baseline_scores) == 0:
        raise ValueError("Input lists cannot be empty")
    
    if seed is not None:
        np.random.seed(seed)
    
    baseline_arr = np.array(baseline_scores)
    post_mod_arr = np.array(post_mod_scores)
    
    # Calculate observed mean difference
    mean_diff_obs = np.mean(post_mod_arr - baseline_arr)
    
    # Paired bootstrap: resample pairs with replacement
    n_pairs = len(baseline_arr)
    bootstrap_diffs = []
    
    for _ in range(n_iterations):
        indices = np.random.choice(n_pairs, size=n_pairs, replace=True)
        boot_baseline = baseline_arr[indices]
        boot_post_mod = post_mod_arr[indices]
        diff = np.mean(boot_post_mod - boot_baseline)
        bootstrap_diffs.append(diff)
    
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Calculate p-value (two-tailed test)
    # p-value = P(|bootstrap_diff| >= |observed_diff|)
    p_value = np.mean(np.abs(bootstrap_diffs) >= np.abs(mean_diff_obs))
    
    # Calculate confidence interval (percentile method)
    ci_lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))
    
    return {
        "p_value": float(p_value),
        "significant": p_value < alpha,
        "mean_baseline": float(np.mean(baseline_arr)),
        "mean_post_mod": float(np.mean(post_mod_arr)),
        "mean_diff": float(mean_diff_obs),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def save_decay_fit_results(
    fit_result: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save exponential decay fit results to a JSON file.
    
    Args:
        fit_result: Dictionary containing fit results
        output_path: Path to output file (default: results/decay_analysis.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = config.get("decay_analysis_path", "results/decay_analysis.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(fit_result, f, indent=2)
    
    return output_path

def save_bootstrap_results(
    bootstrap_result: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save bootstrap test results to a JSON file.
    
    Args:
        bootstrap_result: Dictionary containing bootstrap results
        output_path: Path to output file (default: results/bootstrap_analysis.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = config.get("bootstrap_analysis_path", "results/bootstrap_analysis.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(bootstrap_result, f, indent=2)
    
    return output_path
