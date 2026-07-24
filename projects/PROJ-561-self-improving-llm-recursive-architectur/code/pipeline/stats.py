import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import curve_fit
from scipy.stats import t
import json
import os

from config import PathConfig

def exponential_decay(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Exponential decay model: y = a * exp(-b * x) + c."""
    return a * np.exp(-b * x) + c

def fit_exponential_decay(
    x: np.ndarray, y: np.ndarray, p0: Optional[Tuple[float, float, float]] = None
) -> Tuple[Dict[str, float], Optional[str]]:
    """
    Fit an exponential decay curve to the data.
    Returns fitted parameters and an error message if fitting fails.
    """
    try:
        if p0 is None:
            # Heuristic initial guess
            p0 = (y[0] - y[-1], 0.1, y[-1])

        params, covariance = curve_fit(exponential_decay, x, y, p0=p0, maxfev=5000)
        a, b, c = params
        return {"a": float(a), "b": float(b), "c": float(c)}, None
    except Exception as e:
        return {}, f"Curve fitting failed: {str(e)}"

def detect_plateau_or_degradation(
    metrics: List[float], threshold: float = 0.05
) -> Tuple[int, str]:
    """
    Detect the first cycle where performance plateaus or degrades.
    Returns (cycle_index, status) where status is 'plateau', 'degradation', or 'none'.
    """
    if len(metrics) < 2:
        return -1, "none"

    baseline = metrics[0]
    for i in range(1, len(metrics)):
        current = metrics[i]
        change = (current - baseline) / baseline if baseline != 0 else 0

        if change < -threshold:
            return i, "degradation"
        elif abs(change) < 1e-6:
            return i, "plateau"

    return -1, "none"

def paired_bootstrap_test(
    baseline_scores: List[float],
    post_mod_scores: List[float],
    n_iterations: int = 10000,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform a paired bootstrap test to compare baseline vs post-modification scores.
    Computes the p-value for the null hypothesis that there is no difference.

    Args:
        baseline_scores: List of scores from the baseline model.
        post_mod_scores: List of scores from the modified model.
        n_iterations: Number of bootstrap iterations.
        alpha: Significance level.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - mean_diff: Mean difference (post_mod - baseline)
            - p_value: Two-tailed p-value
            - significant: Boolean indicating if p < alpha
            - confidence_interval: 95% CI of the difference
    """
    if seed is not None:
        np.random.seed(seed)

    if len(baseline_scores) != len(post_mod_scores):
        raise ValueError("Baseline and post-mod scores must have the same length.")

    n = len(baseline_scores)
    diffs = np.array(post_mod_scores) - np.array(baseline_scores)
    mean_diff = np.mean(diffs)

    # Bootstrap resampling of the differences
    bootstrap_means = []
    for _ in range(n_iterations):
        indices = np.random.choice(n, size=n, replace=True)
        sample_diffs = diffs[indices]
        bootstrap_means.append(np.mean(sample_diffs))

    bootstrap_means = np.array(bootstrap_means)

    # Two-tailed p-value: proportion of bootstrap means as extreme as observed mean_diff
    # under the null hypothesis (mean = 0), we shift the bootstrap distribution
    shifted_means = bootstrap_means - np.mean(bootstrap_means)
    extreme_count = np.sum(np.abs(shifted_means) >= np.abs(mean_diff))
    p_value = extreme_count / n_iterations

    # 95% Confidence Interval
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)

    return {
        "mean_diff": float(mean_diff),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
        "confidence_interval": [float(ci_lower), float(ci_upper)],
        "n_iterations": n_iterations,
        "alpha": alpha,
    }

def save_bootstrap_results(
    results: Dict[str, Any], cycle_number: int, output_dir: Optional[str] = None
) -> str:
    """
    Save bootstrap test results to a JSON file.
    Returns the path to the saved file.
    """
    if output_dir is None:
        config = PathConfig()
        output_dir = config.results_dir

    os.makedirs(output_dir, exist_ok=True)
    filename = f"bootstrap_cycle_{cycle_number}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    return filepath

def save_decay_fit_results(
    fit_params: Dict[str, float],
    x_data: np.ndarray,
    y_data: np.ndarray,
    cycle_number: int,
    output_dir: Optional[str] = None,
) -> str:
    """
    Save exponential decay fit results to a JSON file.
    Returns the path to the saved file.
    """
    if output_dir is None:
        config = PathConfig()
        output_dir = config.results_dir

    os.makedirs(output_dir, exist_ok=True)
    filename = f"decay_fit_cycle_{cycle_number}.json"
    filepath = os.path.join(output_dir, filename)

    data = {
        "parameters": fit_params,
        "x_data": x_data.tolist(),
        "y_data": y_data.tolist(),
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return filepath