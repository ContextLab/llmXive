"""
Statistics utilities for the Cortical Column LLM project.

This module provides functions for:
- Loading gradient norms from JSON logs
- Comparing gradient stability between models (KS test)
- Comparing ablation results (paired t-test)
- Calculating scaling exponents from performance data
"""

import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

# Configure logging
logger = logging.getLogger(__name__)


def load_gradient_norms(filepath: str = "data/logs/gradient_norms.json") -> List[float]:
    """
    Load gradient norms from a JSON file.

    Args:
        filepath: Path to the gradient norms JSON file.

    Returns:
        List of gradient norm values.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Gradient norms file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list in {filepath}, got {type(data)}")

    norms = []
    for item in data:
        if isinstance(item, dict) and 'norm' in item:
            norms.append(float(item['norm']))
        elif isinstance(item, (int, float)):
            norms.append(float(item))
        else:
            logger.warning(f"Skipping invalid item in gradient norms: {item}")

    if not norms:
        raise ValueError(f"No valid gradient norms found in {filepath}")

    return norms


def compare_gradient_stability(
    baseline_file: str = "data/logs/gradient_norms.json",
    microcircuit_file: str = "data/logs/gradient_norms_microcircuit.json",
    output_file: str = "data/results/gradient_stability.json"
) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test between baseline and microcircuit gradient norms.

    Args:
        baseline_file: Path to baseline gradient norms JSON.
        microcircuit_file: Path to microcircuit gradient norms JSON.
        output_file: Path to write results JSON.

    Returns:
        Dictionary with ks_statistic, p_value, and stable flag.
    """
    logger.info(f"Comparing gradient stability: {baseline_file} vs {microcircuit_file}")

    baseline_norms = load_gradient_norms(baseline_file)
    microcircuit_norms = load_gradient_norms(microcircuit_file)

    # Perform KS test
    ks_statistic, p_value = stats.ks_2samp(baseline_norms, microcircuit_norms)

    # Determine stability (p > 0.05 means distributions are not significantly different)
    stable = p_value > 0.05

    result = {
        "ks_statistic": float(ks_statistic),
        "p_value": float(p_value),
        "stable": stable,
        "baseline_n": len(baseline_norms),
        "microcircuit_n": len(microcircuit_norms)
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Gradient stability comparison complete. Stable: {stable}, p-value: {p_value:.4f}")

    return result


def compare_ablation_results(
    ablation_results_file: str = "data/results/ablation_results.json",
    output_file: str = "data/results/ablation_stats.json"
) -> Dict[str, Any]:
    """
    Compute difference in MAE between full and ablated models using paired t-test.

    Args:
        ablation_results_file: Path to ablation results JSON.
        output_file: Path to write statistics JSON.

    Returns:
        Dictionary with full_mae, ablated_mae, mae_diff, p_value, and significant flag.
    """
    logger.info(f"Comparing ablation results from {ablation_results_file}")

    if not os.path.exists(ablation_results_file):
        raise FileNotFoundError(f"Ablation results file not found: {ablation_results_file}")

    with open(ablation_results_file, 'r') as f:
        results = json.load(f)

    if not isinstance(results, dict):
        raise ValueError(f"Expected dict in {ablation_results_file}, got {type(results)}")

    # Extract full model MAE (assuming 'full' key exists)
    full_result = results.get('full')
    if full_result is None:
        raise ValueError("'full' variant not found in ablation results")

    full_mae = full_result.get('test_mae')
    if full_mae is None:
        raise ValueError("'test_mae' not found in full variant results")

    # Collect ablated MAEs (excluding 'full')
    ablated_maes = []
    for variant_name, variant_result in results.items():
        if variant_name != 'full':
          test_mae = variant_result.get('test_mae')
          if test_mae is not None:
              ablated_maes.append(test_mae)

    if not ablated_maes:
        raise ValueError("No ablated variants with test_mae found")

    # For paired t-test, we need matched pairs. Since we only have single values per variant,
    # we treat this as a one-sample t-test against the full MAE (testing if ablated differ from full)
    # Alternatively, we can do a two-sample t-test treating them as independent samples
    # Given the context, we'll use two-sample t-test: full (single value replicated) vs ablated
    # But better: compare full vs each ablated individually and aggregate?
    # Let's do: one-sample t-test of (ablated_maes - full_mae) against 0
    differences = [mae - full_mae for mae in ablated_maes]

    t_statistic, p_value = stats.ttest_1samp(differences, 0.0)

    # Calculate average ablated MAE
    ablated_mae = float(np.mean(ablated_maes))
    mae_diff = ablated_mae - full_mae

    significant = p_value < 0.05

    result = {
        "full_mae": float(full_mae),
        "ablated_mae": ablated_mae,
        "mae_diff": float(mae_diff),
        "p_value": float(p_value),
        "significant": significant,
        "n_ablated": len(ablated_maes),
        "t_statistic": float(t_statistic)
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Ablation comparison complete. Significant: {significant}, p-value: {p_value:.4f}")

    return result


def calculate_scaling_exponent(
    scaling_results_file: str = "data/results/scaling_results.json",
    output_file: str = "data/results/scaling_exponent.json"
) -> Dict[str, Any]:
    """
    Fit a power-law model to performance data and calculate scaling exponent.

    Assumes the input file contains results for different model scales (e.g., 1x, 2x, 4x).
    Fits: log(MAE) = intercept + exponent * log(Parameters)

    Args:
        scaling_results_file: Path to scaling results JSON.
        output_file: Path to write exponent JSON.

    Returns:
        Dictionary with exponent, r_squared, confidence_interval, and interpretation.
    """
    logger.info(f"Calculating scaling exponent from {scaling_results_file}")

    if not os.path.exists(scaling_results_file):
        raise FileNotFoundError(f"Scaling results file not found: {scaling_results_file}")

    with open(scaling_results_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list in {scaling_results_file}, got {type(data)}")

    # Extract parameters and MAE for each variant
    params_list = []
    mae_list = []

    for item in data:
        # Handle both dict and list formats
        if isinstance(item, dict):
            params = item.get('parameters') or item.get('num_params')
            mae = item.get('test_mae') or item.get('mae')
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            params = item[0]
            mae = item[1]
        else:
            logger.warning(f"Skipping invalid item: {item}")
            continue

        if params is not None and mae is not None:
            params_list.append(float(params))
            mae_list.append(float(mae))

    if len(params_list) < 2:
        raise ValueError("Need at least 2 data points to calculate scaling exponent")

    # Convert to log space
    log_params = np.log(params_list)
    log_mae = np.log(mae_list)

    # Fit linear model: log(MAE) = exponent * log(Params) + intercept
    # Using scipy's linregress
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_mae)

    exponent = float(slope)
    r_squared = float(r_value ** 2)

    # Calculate 95% confidence interval for the slope
    n = len(log_params)
    t_critical = stats.t.ppf(0.975, n - 2)
    confidence_interval = (
        exponent - t_critical * std_err,
        exponent + t_critical * std_err
    )

    # Interpret the exponent
    # If exponent ~ 0: MAE doesn't change with size (neutral)
    # If exponent < 0: MAE decreases with size (improvement)
    # If exponent > 0: MAE increases with size (degradation)
    if abs(exponent) < 0.1:
        interpretation = "neutral"
    elif exponent < 0:
        interpretation = "sublinear_improvement"
    else:
        interpretation = "superlinear_degradation"

    result = {
        "exponent": exponent,
        "r_squared": r_squared,
        "p_value": float(p_value),
        "std_err": float(std_err),
        "confidence_interval": {
            "lower": confidence_interval[0],
            "upper": confidence_interval[1]
        },
        "interpretation": interpretation,
        "n_points": n,
        "log_params_range": [float(min(log_params)), float(max(log_params))],
        "log_mae_range": [float(min(log_mae)), float(max(log_mae))]
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Scaling exponent calculated: {exponent:.4f} ({interpretation})")

    return result


def main():
    """Main entry point for running statistics analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run statistics analysis for cortical column experiments")
    parser.add_argument('--gradient-comparison', action='store_true',
                        help='Compare gradient stability between baseline and microcircuit')
    parser.add_argument('--ablation-comparison', action='store_true',
                        help='Compare ablation results')
    parser.add_argument('--scaling-exponent', action='store_true',
                        help='Calculate scaling exponent')
    parser.add_argument('--baseline-file', type=str, default='data/logs/gradient_norms.json',
                        help='Path to baseline gradient norms file')
    parser.add_argument('--microcircuit-file', type=str, default='data/logs/gradient_norms_microcircuit.json',
                        help='Path to microcircuit gradient norms file')
    parser.add_argument('--ablation-file', type=str, default='data/results/ablation_results.json',
                        help='Path to ablation results file')
    parser.add_argument('--scaling-file', type=str, default='data/results/scaling_results.json',
                        help='Path to scaling results file')
    parser.add_argument('--output-dir', type=str, default='data/results',
                        help='Output directory for results')

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    results = {}

    if args.gradient_comparison:
        baseline_file = args.baseline_file
        microcircuit_file = args.microcircuit_file
        output_file = os.path.join(args.output_dir, 'gradient_stability.json')
        results['gradient_stability'] = compare_gradient_stability(baseline_file, microcircuit_file, output_file)

    if args.ablation_comparison:
        ablation_file = args.ablation_file
        output_file = os.path.join(args.output_dir, 'ablation_stats.json')
        results['ablation_stats'] = compare_ablation_results(ablation_file, output_file)

    if args.scaling_exponent:
        scaling_file = args.scaling_file
        output_file = os.path.join(args.output_dir, 'scaling_exponent.json')
        results['scaling_exponent'] = calculate_scaling_exponent(scaling_file, output_file)

    if not args.gradient_comparison and not args.ablation_comparison and not args.scaling_exponent:
        parser.print_help()
        return 1

    logger.info(f"Analysis complete. Results: {results}")
    return 0


if __name__ == '__main__':
    exit(main())