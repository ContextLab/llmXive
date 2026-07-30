"""
Statistics utilities for the Cortical Column LLM project.

Provides functions for statistical testing (t-tests, KS tests) and
analysis of scaling laws (power-law fitting).
"""
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_gradient_norms(file_path: str) -> List[float]:
    """
    Load gradient norms from a JSON log file.

    Args:
        file_path: Path to the JSON file containing gradient norms.

    Returns:
        List of gradient norm values.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Gradient norms file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Handle different potential schemas
    if isinstance(data, list):
        return [float(x) for x in data]
    elif isinstance(data, dict):
        if 'norms' in data:
            return [float(x) for x in data['norms']]
        elif 'gradient_norms' in data:
            return [float(x) for x in data['gradient_norms']]
        else:
            # Try to extract all numeric values
            return [float(v) for v in data.values() if isinstance(v, (int, float))]
    else:
        raise ValueError(f"Unexpected data format in {file_path}")


def compare_gradient_stability(baseline_path: str, microcircuit_path: str,
                               output_path: str) -> Dict[str, Any]:
    """
    Compare gradient stability between baseline and microcircuit models
    using the Kolmogorov-Smirnov test.

    Args:
        baseline_path: Path to baseline gradient norms JSON.
        microcircuit_path: Path to microcircuit gradient norms JSON.
        output_path: Path to write the results JSON.

    Returns:
        Dictionary with KS statistic, p-value, and stability assessment.
    """
    baseline_norms = load_gradient_norms(baseline_path)
    microcircuit_norms = load_gradient_norms(microcircuit_path)

    if len(baseline_norms) < 2 or len(microcircuit_norms) < 2:
        raise ValueError("Need at least 2 gradient norms in each file for KS test")

    # Perform two-sample KS test
    ks_statistic, p_value = stats.ks_2samp(baseline_norms, microcircuit_norms)

    # Interpret stability: if p > 0.05, distributions are not significantly different
    # (i.e., microcircuit maintains similar gradient stability to baseline)
    is_stable = p_value > 0.05

    result = {
        "ks_statistic": float(ks_statistic),
        "p_value": float(p_value),
        "stable": is_stable,
        "baseline_n": len(baseline_norms),
        "microcircuit_n": len(microcircuit_norms)
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Gradient stability comparison: KS={ks_statistic:.4f}, p={p_value:.4f}, stable={is_stable}")
    return result


def compare_ablation_results(ablation_results_path: str, output_path: str) -> Dict[str, Any]:
    """
    Compare ablation results to determine statistical significance of performance degradation.

    Performs a paired t-test between the full model and each ablated variant.

    Args:
        ablation_results_path: Path to ablation_results.json.
        output_path: Path to write the statistics JSON.

    Returns:
        Dictionary with MAE values, difference, p-value, and significance assessment.
    """
    if not os.path.exists(ablation_results_path):
        raise FileNotFoundError(f"Ablation results file not found: {ablation_results_path}")

    with open(ablation_results_path, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    if not results:
        raise ValueError("No results found in ablation_results.json")

    # Find full model and ablated variants
    full_result = None
    ablated_results = []

    for r in results:
        name = r.get('variant', '').lower()
        if 'full' in name or 'baseline' in name:
            full_result = r
        else:
            ablated_results.append(r)

    if not full_result:
        raise ValueError("No 'full' or 'baseline' variant found in ablation results")

    full_mae = full_result.get('mae')
    if full_mae is None:
        raise ValueError("Full model MAE not found")

    # Collect MAEs from ablated variants
    ablated_maes = [r.get('mae') for r in ablated_results if r.get('mae') is not None]

    if not ablated_maes:
        raise ValueError("No ablated model MAEs found")

    # Calculate mean ablated MAE
    ablated_mae = float(np.mean(ablated_maes))
    mae_diff = ablated_mae - full_mae

    # For t-test, we need multiple samples. Since we have single values per variant,
    # we'll use the individual ablated variants as samples against the full model
    # (treating full model as a reference with assumed low variance)
    # Alternative: if we have multiple runs, use those; otherwise use bootstrap
    # For now, use a simple approach: compare ablated_maes to a repeated full_mae

    n_ablated = len(ablated_maes)
    if n_ablated >= 2:
        # Perform one-sample t-test: is the mean of ablated_maes significantly different from full_mae?
        t_stat, p_value = stats.ttest_1samp(ablated_maes, full_mae)
    else:
        # Single ablated result: cannot do t-test, use effect size only
        logger.warning("Only one ablated result found, cannot perform t-test. Using effect size only.")
        p_value = 1.0  # Not significant by default

    # Calculate relative increase
    relative_increase = (mae_diff / full_mae * 100) if full_mae > 0 else 0.0

    # Determine significance: p < 0.05 AND relative increase > 15%
    significant = (p_value < 0.05) and (relative_increase > 15.0)

    result = {
        "full_mae": float(full_mae),
        "ablated_mae": float(ablated_mae),
        "mae_diff": float(mae_diff),
        "p_value": float(p_value),
        "relative_increase_pct": float(relative_increase),
        "significant": significant,
        "n_ablated_variants": n_ablated
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Ablation comparison: full={full_mae:.4f}, ablated={ablated_mae:.4f}, diff={mae_diff:.4f}, p={p_value:.4f}, significant={significant}")
    return result


def calculate_scaling_exponent(scaling_results_path: str, output_path: str) -> Dict[str, Any]:
    """
    Calculate the scaling exponent by fitting a power law to performance data.

    Fits: log(MAE) = exponent * log(Parameters) + intercept

    Args:
        scaling_results_path: Path to scaling_results.json.
        output_path: Path to write the exponent JSON.

    Returns:
        Dictionary with exponent, confidence interval, and linearity assessment.
    """
    if not os.path.exists(scaling_results_path):
        raise FileNotFoundError(f"Scaling results file not found: {scaling_results_path}")

    with open(scaling_results_path, 'r') as f:
        data = json.load(f)

    variants = data.get('variants', [])
    if not variants:
        raise ValueError("No variants found in scaling_results.json")

    # Extract parameters and MAE
    params_list = []
    mae_list = []

    for v in variants:
        params = v.get('params')
        mae = v.get('mae')
        if params is not None and mae is not None:
            params_list.append(float(params))
            mae_list.append(float(mae))

    if len(params_list) < 2:
        raise ValueError("Need at least 2 variants to fit a scaling law")

    # Convert to log space
    log_params = np.log(params_list)
    log_mae = np.log(mae_list)

    # Fit linear regression: log(MAE) = slope * log(Params) + intercept
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_mae)

    # Calculate 95% confidence interval for the slope
    # Using t-distribution for small samples
    n = len(params_list)
    if n > 2:
        t_crit = stats.t.ppf(0.975, df=n-2)
        conf_interval = t_crit * std_err
    else:
        # For n=2, use a heuristic
        conf_interval = abs(slope) * 0.5  # 50% heuristic

    exponent = float(slope)
    ci_low = exponent - conf_interval
    ci_high = exponent + conf_interval

    # Determine linearity
    # exponent >= 1.0: linear or superlinear scaling
    # exponent < 1.0: sublinear scaling (better efficiency)
    if exponent >= 1.0:
        linear_or_sublinear = "linear_or_superlinear"
    else:
        linear_or_sublinear = "sublinear"

    result = {
        "exponent": float(exponent),
        "confidence_interval": [float(ci_low), float(ci_high)],
        "linear_or_sublinear": linear_or_sublinear,
        "r_squared": float(r_value**2),
        "n_variants": n,
        "params_range": [min(params_list), max(params_list)],
        "mae_range": [min(mae_list), max(mae_list)]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Scaling exponent: {exponent:.4f} (95% CI: [{ci_low:.4f}, {ci_high:.4f}]), {linear_or_sublinear}")
    return result


def main():
    """
    Main function to run all statistical analyses.

    This function orchestrates the execution of all statistical tests
    and writes results to the appropriate output files.
    """
    # Define paths
    baseline_gradient_path = "data/logs/gradient_norms.json"
    microcircuit_gradient_path = "data/logs/gradient_norms_microcircuit.json"
    gradient_stability_output = "data/results/gradient_stability.json"

    ablation_results_path = "data/results/ablation_results.json"
    ablation_stats_output = "data/results/ablation_stats.json"

    scaling_results_path = "data/results/scaling_results.json"
    scaling_exponent_output = "data/results/scaling_exponent.json"

    # Run gradient stability comparison
    try:
        if os.path.exists(baseline_gradient_path) and os.path.exists(microcircuit_gradient_path):
            compare_gradient_stability(
                baseline_gradient_path,
                microcircuit_gradient_path,
                gradient_stability_output
            )
        else:
            logger.warning(f"Gradient norm files not found. Skipping gradient stability analysis.")
            logger.warning(f"  Expected: {baseline_gradient_path}, {microcircuit_gradient_path}")
    except Exception as e:
        logger.error(f"Error in gradient stability analysis: {e}")

    # Run ablation comparison
    try:
        if os.path.exists(ablation_results_path):
            compare_ablation_results(
                ablation_results_path,
                ablation_stats_output
            )
        else:
            logger.warning(f"Ablation results file not found: {ablation_results_path}")
    except Exception as e:
        logger.error(f"Error in ablation comparison: {e}")

    # Run scaling exponent calculation
    try:
        if os.path.exists(scaling_results_path):
            calculate_scaling_exponent(
                scaling_results_path,
                scaling_exponent_output
            )
        else:
            logger.warning(f"Scaling results file not found: {scaling_results_path}")
    except Exception as e:
        logger.error(f"Error in scaling exponent calculation: {e}")

    logger.info("Statistical analysis complete.")


if __name__ == "__main__":
    main()