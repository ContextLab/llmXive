"""
Analysis module for computing error rates, confidence intervals, and statistical tests.

This module provides functions to load simulation results, calculate Type I and Type II
error rates, compute bootstrap confidence intervals, and perform Kolmogorov-Smirnov tests
on p-value distributions.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_simulation_results(result_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load simulation results from a JSON file.

    Args:
        result_path: Path to the JSON file containing simulation results.

    Returns:
        Dictionary containing the loaded simulation results.

    Raises:
        FileNotFoundError: If the result file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(result_path)
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {path}")

    with open(path, 'r') as f:
        return json.load(f)

def calculate_error_rates(p_values: List[float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate empirical error rates from a list of p-values.

    Args:
        p_values: List of p-values from hypothesis tests.
        alpha: Significance level threshold (default 0.05).

    Returns:
        Dictionary with 'error_rate' (proportion of p < alpha) and 'n_tests' (count).
    """
    if not p_values:
        return {'error_rate': 0.0, 'n_tests': 0}

    p_array = np.array(p_values)
    errors = np.sum(p_array < alpha)
    n_tests = len(p_array)
    error_rate = errors / n_tests if n_tests > 0 else 0.0

    return {
        'error_rate': float(error_rate),
        'n_tests': int(n_tests)
    }

def calculate_bootstrap_ci(
    p_values: List[float],
    alpha: float = 0.05,
    n_bootstraps: int = 1000,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for error rates.

    Args:
        p_values: List of p-values from hypothesis tests.
        alpha: Significance level threshold (default 0.05).
        n_bootstraps: Number of bootstrap iterations (default 1000).
        confidence_level: Confidence level for CI (default 0.95).

    Returns:
        Dictionary with 'error_rate', 'ci_lower', 'ci_upper', and 'n_bootstraps'.
    """
    if not p_values:
        return {
            'error_rate': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'n_bootstraps': 0
        }

    p_array = np.array(p_values)
    n = len(p_array)
    error_rates = []

    for _ in range(n_bootstraps):
        # Resample with replacement
        sample = np.random.choice(p_array, size=n, replace=True)
        errors = np.sum(sample < alpha)
        error_rates.append(errors / n)

    error_rates = np.array(error_rates)
    lower_percentile = (1 - confidence_level) / 2 * 100
    upper_percentile = (1 + confidence_level) / 2 * 100

    return {
        'error_rate': float(np.mean(error_rates)),
        'ci_lower': float(np.percentile(error_rates, lower_percentile)),
        'ci_upper': float(np.percentile(error_rates, upper_percentile)),
        'n_bootstraps': n_bootstraps
    }

def ks_test_wrapper(p_values_baseline: List[float], p_values_augmented: List[float]) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test to compare two p-value distributions.

    Args:
        p_values_baseline: List of p-values from baseline condition.
        p_values_augmented: List of p-values from augmented condition.

    Returns:
        Dictionary with 'statistic', 'p_value', and 'significant' (boolean at alpha=0.05).

    Raises:
        ValueError: If inputs are not lists/arrays of p-values.
    """
    if not isinstance(p_values_baseline, (list, np.ndarray)) or not isinstance(p_values_augmented, (list, np.ndarray)):
        raise ValueError("Inputs must be lists or arrays of p-values")

    if len(p_values_baseline) == 0 or len(p_values_augmented) == 0:
        raise ValueError("Input lists must not be empty")

    # Validate that inputs look like p-values (between 0 and 1)
    baseline_arr = np.array(p_values_baseline)
    augmented_arr = np.array(p_values_augmented)

    if not np.all((baseline_arr >= 0) & (baseline_arr <= 1)):
        raise ValueError("Baseline p-values must be in range [0, 1]")
    if not np.all((augmented_arr >= 0) & (augmented_arr <= 1)):
        raise ValueError("Augmented p-values must be in range [0, 1]")

    statistic, p_value = stats.ks_2samp(baseline_arr, augmented_arr)

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05)
    }

def analyze_baseline_results(
    result_path: Union[str, Path],
    condition_type: str
) -> Dict[str, Any]:
    """
    Analyze baseline simulation results for a specific condition (null or alt).

    Args:
        result_path: Path to the baseline result JSON file.
        condition_type: Type of condition ('null' for Type I, 'alt' for Type II).

    Returns:
        Dictionary containing error rates, confidence intervals, and metadata.
    """
    results = load_simulation_results(result_path)

    if condition_type not in results:
        raise ValueError(f"Condition type '{condition_type}' not found in results")

    condition_data = results[condition_type]
    p_values = condition_data.get('p_values', [])

    error_rates = calculate_error_rates(p_values)
    bootstrap_ci = calculate_bootstrap_ci(p_values)

    return {
        'condition_type': condition_type,
        'error_rates': error_rates,
        'bootstrap_ci': bootstrap_ci,
        'metadata': results.get('metadata', {})
    }

def generate_report(
    baseline_results: Dict[str, Any],
    augmented_results: List[Dict[str, Any]],
    threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Generate a comprehensive comparative analysis report.

    Args:
        baseline_results: Dictionary containing baseline analysis results.
        augmented_results: List of dictionaries containing augmented analysis results.
        threshold: Fixed design threshold for Type I error (default 0.10).

    Returns:
        Dictionary containing the complete analysis report.
    """
    report = {
        'baseline': baseline_results,
        'augmented_comparisons': [],
        'threshold_analysis': {
            'threshold_value': threshold,
            'violations': []
        },
        'summary': {}
    }

    baseline_error_rate = baseline_results.get('error_rates', {}).get('error_rate', 0.0)

    for aug_result in augmented_results:
        aug_error_rate = aug_result.get('error_rates', {}).get('error_rate', 0.0)
        difference = aug_error_rate - baseline_error_rate

        comparison = {
            'method': aug_result.get('method', 'unknown'),
            'augmented_error_rate': aug_error_rate,
            'baseline_error_rate': baseline_error_rate,
            'difference': difference,
            'exceeds_threshold': aug_error_rate > threshold,
            'confidence_interval': aug_result.get('bootstrap_ci', {})
        }

        report['augmented_comparisons'].append(comparison)

        if aug_error_rate > threshold:
            report['threshold_analysis']['violations'].append({
                'method': aug_result.get('method', 'unknown'),
                'error_rate': aug_error_rate,
                'threshold': threshold,
                'excess': aug_error_rate - threshold
            })

    # Generate summary
    report['summary'] = {
        'total_comparisons': len(augmented_results),
        'violations_count': len(report['threshold_analysis']['violations']),
        'baseline_error_rate': baseline_error_rate,
        'max_augmented_error_rate': max(
            [r.get('error_rates', {}).get('error_rate', 0.0) for r in augmented_results],
            default=0.0
        )
    }

    return report

def main() -> None:
    """
    Main entry point for the analysis module.

    This function demonstrates the usage of the analysis functions by loading
    sample results and generating a report. In practice, this would be called
    from the main pipeline script with actual result paths.
    """
    logger.info("Analysis module loaded successfully")
    logger.info("Available functions: load_simulation_results, calculate_error_rates, "
               "calculate_bootstrap_ci, ks_test_wrapper, analyze_baseline_results, generate_report")

    # Example usage (would be replaced with actual paths in production)
    # result_path = "results/example_baseline_null.json"
    # if os.path.exists(result_path):
    #     analysis = analyze_baseline_results(result_path, 'null')
    #     logger.info(f"Analysis result: {analysis}")

if __name__ == "__main__":
    main()