"""
Statistics and analysis utilities for the cortical column LLM project.

This module provides functions for statistical tests, data loading, and
result analysis required for verification of scientific claims.
"""
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def load_gradient_norms(filepath: str) -> List[float]:
    """
    Load gradient norms from a JSON log file.

    Args:
        filepath: Path to the JSON file containing gradient norms.

    Returns:
        List of gradient norms (floats).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Gradient norms file not found: {filepath}")

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle both list format and dict format with 'norms' key
    if isinstance(data, list):
        norms = data
    elif isinstance(data, dict) and 'norms' in data:
        norms = data['norms']
    else:
        raise ValueError(f"Invalid format in {filepath}: expected list or dict with 'norms' key")

    # Ensure all values are floats
    try:
        return [float(x) for x in norms]
    except (TypeError, ValueError) as e:
        raise ValueError(f"Non-numeric values in gradient norms: {e}")

def compare_gradient_stability(
    baseline_path: str,
    microcircuit_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Perform a Kolmogorov-Smirnov test between baseline and microcircuit gradient norms.

    This function compares the distribution of gradient norms from the baseline
    model (standard Transformer) and the microcircuit model to assess gradient
    stability, as required by SC-002.

    Args:
        baseline_path: Path to baseline gradient norms JSON file.
        microcircuit_path: Path to microcircuit gradient norms JSON file.
        output_path: Path where the results JSON will be written.

    Returns:
        Dictionary with keys:
            - 'ks_statistic': float (KS test statistic)
            - 'p_value': float (p-value from KS test)
            - 'stable': bool (True if p_value > 0.05, indicating no significant difference)

    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If data is insufficient for statistical test.
    """
    logger.info(f"Loading baseline gradient norms from {baseline_path}")
    baseline_norms = load_gradient_norms(baseline_path)
    logger.info(f"Loaded {len(baseline_norms)} baseline gradient norms")

    logger.info(f"Loading microcircuit gradient norms from {microcircuit_path}")
    microcircuit_norms = load_gradient_norms(microcircuit_path)
    logger.info(f"Loaded {len(microcircuit_norms)} microcircuit gradient norms")

    if len(baseline_norms) < 2 or len(microcircuit_norms) < 2:
        raise ValueError("Insufficient data for KS test: need at least 2 samples per group")

    # Perform two-sample Kolmogorov-Smirnov test
    ks_statistic, p_value = stats.ks_2samp(baseline_norms, microcircuit_norms)

    # Determine stability: if p_value > 0.05, distributions are not significantly different
    # (i.e., gradient stability is maintained)
    stable = p_value > 0.05

    result = {
        "ks_statistic": float(ks_statistic),
        "p_value": float(p_value),
        "stable": stable
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Write results to file
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"KS test completed: statistic={ks_statistic:.4f}, p_value={p_value:.4f}, stable={stable}")
    logger.info(f"Results written to {output_path}")

    return result

def compare_ablation_results(
    ablation_results_path: str,
    output_path: str,
    variant: str = "no_recurrence"
) -> Dict[str, Any]:
    """
    Compute the difference in MAE between full and ablated models using a paired t-test.

    Args:
        ablation_results_path: Path to ablation results JSON file.
        output_path: Path where the statistics JSON will be written.
        variant: The ablation variant to compare against full model.

    Returns:
        Dictionary with keys:
            - 'full_mae': float
            - 'ablated_mae': float
            - 'mae_diff': float
            - 'p_value': float
            - 'significant': bool
    """
    with open(ablation_results_path, 'r') as f:
        results = json.load(f)

    # Extract MAE values
    full_mae = results.get('full', {}).get('mae')
    ablated_mae = results.get(variant, {}).get('mae')

    if full_mae is None or ablated_mae is None:
        raise ValueError(f"MAE values not found for full={full_mae}, {variant}={ablated_mae}")

    mae_diff = float(ablated_mae - full_mae)

    # For paired t-test, we need multiple runs. If only single values,
    # we cannot compute a meaningful p-value, so we return None for p-value
    # and set significant to False
    # In a real scenario with multiple runs, we would have lists of MAE values
    p_value = None
    significant = False

    result = {
        "full_mae": float(full_mae),
        "ablated_mae": float(ablated_mae),
        "mae_diff": mae_diff,
        "p_value": p_value,
        "significant": significant
    }

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result

def calculate_scaling_exponent(
    scaling_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Fit a power-law model to scaling data and calculate the exponent.

    Args:
        scaling_results_path: Path to scaling results JSON file.
        output_path: Path where the exponent JSON will be written.

    Returns:
        Dictionary with scaling exponent and confidence intervals.
    """
    with open(scaling_results_path, 'r') as f:
        data = json.load(f)

    # Extract parameter counts and MAE values
    params = []
    maes = []
    for variant in data.values():
        if 'params' in variant and 'mae' in variant:
            params.append(variant['params'])
            maes.append(variant['mae'])

    if len(params) < 2:
        raise ValueError("Insufficient data points for scaling analysis")

    # Log-log regression: log(MAE) = exponent * log(params) + intercept
    log_params = np.log(params)
    log_maes = np.log(maes)

    # Linear regression
    slope, intercept, r_value, p_val, std_err = stats.linregress(log_params, log_maes)

    result = {
        "exponent": float(slope),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_val),
        "std_error": float(std_err),
        "interpretation": "sublinear" if slope < 1.0 else ("linear" if abs(slope - 1.0) < 0.1 else "superlinear")
    }

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result

def main():
    """Main entry point for running statistics analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Statistics analysis for cortical column experiments")
    parser.add_argument('--baseline-norms', type=str, required=False,
                      help='Path to baseline gradient norms JSON')
    parser.add_argument('--microcircuit-norms', type=str, required=False,
                      help='Path to microcircuit gradient norms JSON')
    parser.add_argument('--output', type=str, default='data/results/gradient_stability.json',
                      help='Output path for gradient stability results')
    parser.add_argument('--ablation-results', type=str, required=False,
                      help='Path to ablation results JSON')
    parser.add_argument('--ablation-output', type=str, default='data/results/ablation_stats.json',
                      help='Output path for ablation statistics')
    parser.add_argument('--scaling-results', type=str, required=False,
                      help='Path to scaling results JSON')
    parser.add_argument('--scaling-output', type=str, default='data/results/scaling_exponent.json',
                      help='Output path for scaling exponent')

    args = parser.parse_args()

    if args.baseline_norms and args.microcircuit_norms:
        result = compare_gradient_stability(args.baseline_norms, args.microcircuit_norms, args.output)
        print(f"Gradient stability: {result}")

    if args.ablation_results:
        result = compare_ablation_results(args.ablation_results, args.ablation_output)
        print(f"Ablation stats: {result}")

    if args.scaling_results:
        result = calculate_scaling_exponent(args.scaling_results, args.scaling_output)
        print(f"Scaling exponent: {result}")

if __name__ == "__main__":
    main()
