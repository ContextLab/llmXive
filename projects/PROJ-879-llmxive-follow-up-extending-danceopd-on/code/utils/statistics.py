import os
import sys
import json
import time
import signal
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from scipy import stats
from scipy.stats import ttest_rel, ttest_ind
import pandas as pd

class TimeoutError(Exception):
    """Custom timeout error for statistical tests."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Statistical test timed out")

def calculate_effect_size(mean_diff: float, std_diff: float) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        mean_diff: Mean difference between paired samples
        std_diff: Standard deviation of the differences
        
    Returns:
        Cohen's d effect size
    """
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff

def bootstrap_power_analysis(
    differences: np.ndarray,
    n_iterations: int = 1000,
    target_power: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform bootstrap power analysis to determine if sample size is sufficient.
    
    Args:
        differences: Array of paired differences
        n_iterations: Number of bootstrap iterations
        target_power: Target statistical power (default 0.8)
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with power analysis results
    """
    n = len(differences)
    if n < 2:
        return {
            "power": 0.0,
            "sample_size": n,
            "sufficient": False,
            "message": "Insufficient sample size for power analysis"
        }
    
    # Bootstrap resampling to estimate power
    bootstrap_means = []
    for _ in range(n_iterations):
        resample = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    # Calculate power based on the proportion of bootstrap means that are significant
    mean_diff = np.mean(differences)
    std_err = np.std(bootstrap_means, ddof=1)
    
    if std_err == 0:
        power = 1.0 if mean_diff != 0 else 0.0
    else:
        # Calculate z-score for the observed mean under the null hypothesis
        z = mean_diff / std_err
        # Power is the probability of rejecting the null when it's false
        power = 1 - stats.norm.cdf(stats.norm.ppf(1 - alpha/2) - abs(z)) + \
                stats.norm.cdf(-stats.norm.ppf(1 - alpha/2) - abs(z))
    
    return {
        "power": float(power),
        "sample_size": n,
        "sufficient": power >= target_power,
        "target_power": target_power,
        "alpha": alpha,
        "mean_difference": float(mean_diff),
        "std_error": float(std_err)
    }

def run_bootstrap_test(
    tree_metrics: List[float],
    teacher_metrics: List[float],
    n_iterations: int = 1000,
    alpha: float = 0.05,
    target_power: float = 0.8
) -> Dict[str, Any]:
    """
    Run bootstrap hypothesis test on FID distributions.
    
    Args:
        tree_metrics: List of FID scores from tree-generated images
        teacher_metrics: List of FID scores from teacher-baseline images
        n_iterations: Number of bootstrap iterations
        alpha: Significance level
        target_power: Target statistical power
        
    Returns:
        Dictionary with bootstrap test results including p-value and confidence intervals
    """
    if len(tree_metrics) != len(teacher_metrics):
        raise ValueError("Tree and teacher metric lists must have the same length")
    
    if len(tree_metrics) == 0:
        return {
            "status": "error",
            "message": "No data provided for bootstrap test"
        }
    
    # Calculate differences
    differences = np.array(teacher_metrics) - np.array(tree_metrics)
    
    # Bootstrap resampling for confidence intervals
    bootstrap_means = []
    n = len(differences)
    
    for _ in range(n_iterations):
        resample = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(np.mean(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    
    # Calculate p-value (two-tailed)
    # Under null hypothesis, mean difference is 0
    z_stat = mean_diff / (std_diff / np.sqrt(n)) if std_diff > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Calculate 95% confidence interval
    ci_lower = np.percentile(bootstrap_means, (alpha/2) * 100)
    ci_upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
    
    # Effect size (Cohen's d)
    effect_size = calculate_effect_size(mean_diff, std_diff)
    
    # Power analysis
    power_result = bootstrap_power_analysis(differences, n_iterations, target_power, alpha)
    
    return {
        "test_type": "bootstrap",
        "status": "success",
        "p_value": float(p_value),
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "confidence_interval": {
            "level": 1 - alpha,
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        },
        "effect_size": float(effect_size),
        "power_analysis": power_result,
        "sample_size": n,
        "iterations": n_iterations,
        "alpha": alpha,
        "significant": p_value < alpha
    }

def run_ttest(
    tree_metrics: List[float],
    teacher_metrics: List[float],
    alpha: float = 0.05,
    target_power: float = 0.8
) -> Dict[str, Any]:
    """
    Run paired t-test on CLIP scores.
    
    Args:
        tree_metrics: List of CLIP scores from tree-generated images
        teacher_metrics: List of CLIP scores from teacher-baseline images
        alpha: Significance level
        target_power: Target statistical power
        
    Returns:
        Dictionary with t-test results including p-value and confidence intervals
    """
    if len(tree_metrics) != len(teacher_metrics):
        raise ValueError("Tree and teacher metric lists must have the same length")
    
    if len(tree_metrics) == 0:
        return {
            "status": "error",
            "message": "No data provided for t-test"
        }
    
    # Paired t-test
    t_stat, p_value = ttest_rel(tree_metrics, teacher_metrics)
    
    # Calculate effect size (Cohen's d for paired samples)
    differences = np.array(teacher_metrics) - np.array(tree_metrics)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    effect_size = calculate_effect_size(mean_diff, std_diff)
    
    # Calculate 95% confidence interval for mean difference
    n = len(differences)
    se = std_diff / np.sqrt(n) if std_diff > 0 else 0
    t_crit = stats.t.ppf(1 - alpha/2, n - 1)
    ci_lower = mean_diff - t_crit * se
    ci_upper = mean_diff + t_crit * se
    
    # Power analysis
    power_result = bootstrap_power_analysis(differences, 1000, target_power, alpha)
    
    return {
        "test_type": "paired_ttest",
        "status": "success",
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "confidence_interval": {
            "level": 1 - alpha,
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        },
        "effect_size": float(effect_size),
        "power_analysis": power_result,
        "sample_size": n,
        "degrees_of_freedom": n - 1,
        "alpha": alpha,
        "significant": p_value < alpha
    }

def save_partial_results(results: Dict[str, Any], output_path: Path, status: str = "partial"):
    """
    Save partial results when timeout or power insufficiency occurs.
    
    Args:
        results: Dictionary of results to save
        output_path: Path to save the results
        status: Status flag (default "partial")
    """
    results["status"] = status
    results["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def save_statistical_tests(
    bootstrap_result: Dict[str, Any],
    ttest_result: Dict[str, Any],
    output_path: Path
):
    """
    Save final statistical test outputs to JSON file.
    
    Args:
        bootstrap_result: Results from bootstrap test
        ttest_result: Results from t-test
        output_path: Path to save the results
    """
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bootstrap_test": bootstrap_result,
        "paired_ttest": ttest_result,
        "summary": {
            "fid_test_significant": bootstrap_result.get("significant", False),
            "clip_test_significant": ttest_result.get("significant", False),
            "fid_p_value": bootstrap_result.get("p_value"),
            "clip_p_value": ttest_result.get("p_value"),
            "fid_confidence_interval": bootstrap_result.get("confidence_interval"),
            "clip_confidence_interval": ttest_result.get("confidence_interval"),
            "fid_effect_size": bootstrap_result.get("effect_size"),
            "clip_effect_size": ttest_result.get("effect_size"),
            "fid_power_sufficient": bootstrap_result.get("power_analysis", {}).get("sufficient", False),
            "clip_power_sufficient": ttest_result.get("power_analysis", {}).get("sufficient", False)
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)