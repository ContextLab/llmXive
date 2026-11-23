"""
Bootstrap Aggregator Module.

This module consolidates aggregation logic for power curve generation,
extracting it from the power_curve_generator to provide a clean API
for multi-kernel and multi-alpha runs.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure imports from sibling modules match the API surface
# Note: We do not import numpy directly here unless used for specific stats,
# relying on the calling context or statsmodels for heavy lifting if needed.
# However, for confidence intervals, we might need numpy/scipy.
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("numpy not available; confidence intervals will be approximate or skipped.")

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logging.warning("scipy not available; confidence intervals will be approximate or skipped.")

logger = logging.getLogger(__name__)


def aggregate_power_results(
    iteration_results: List[Dict[str, Any]],
    sample_size: int,
    kernel: str,
    alpha: float
) -> Dict[str, Any]:
    """
    Aggregate results from multiple bootstrap iterations for a specific configuration.

    Args:
        iteration_results: List of dictionaries containing individual iteration results.
                           Expected keys: 'replication_success' (bool), 'effect_size' (float), 'p_value' (float).
        sample_size: The sample size used for this configuration.
        kernel: The smoothing kernel used (e.g., '4s', '8s').
        alpha: The significance threshold used.

    Returns:
        A dictionary containing aggregated metrics:
        - 'sample_size': int
        - 'kernel': str
        - 'alpha': float
        - 'total_iterations': int
        - 'successful_replications': int
        - 'empirical_power': float (rate of successful replications)
        - 'mean_effect_size': float (average of effect sizes from successful iterations)
        - 'std_effect_size': float (standard deviation of effect sizes)
        - 'mean_p_value': float
    """
    if not iteration_results:
        logger.warning(f"No results to aggregate for N={sample_size}, kernel={kernel}, alpha={alpha}")
        return {
            "sample_size": sample_size,
            "kernel": kernel,
            "alpha": alpha,
            "total_iterations": 0,
            "successful_replications": 0,
            "empirical_power": 0.0,
            "mean_effect_size": 0.0,
            "std_effect_size": 0.0,
            "mean_p_value": 0.0,
            "status": "empty"
        }

    successful_count = sum(1 for r in iteration_results if r.get('replication_success', False))
    total_count = len(iteration_results)
    empirical_power = successful_count / total_count if total_count > 0 else 0.0

    # Extract effect sizes from successful iterations only, or all?
    # Typically power analysis looks at the rate, but effect size stability is also key.
    # Let's calculate mean effect size across ALL successful iterations.
    effect_sizes = [r.get('effect_size', 0.0) for r in iteration_results if r.get('replication_success', False)]

    mean_effect = float(np.mean(effect_sizes)) if HAS_NUMPY and effect_sizes else 0.0
    std_effect = float(np.std(effect_sizes)) if HAS_NUMPY and len(effect_sizes) > 1 else 0.0

    p_values = [r.get('p_value', 1.0) for r in iteration_results if r.get('replication_success', False)]
    mean_p = float(np.mean(p_values)) if HAS_NUMPY and p_values else 1.0

    return {
        "sample_size": sample_size,
        "kernel": kernel,
        "alpha": alpha,
        "total_iterations": total_count,
        "successful_replications": successful_count,
        "empirical_power": empirical_power,
        "mean_effect_size": mean_effect,
        "std_effect_size": std_effect,
        "mean_p_value": mean_p,
        "status": "aggregated"
    }


def compute_confidence_intervals(
    results: List[Dict[str, Any]],
    alpha_threshold: float = 0.05
) -> Dict[str, float]:
    """
    Compute confidence intervals for the empirical power estimate.

    Uses the Clopper-Pearson exact interval if possible, or Normal approximation.

    Args:
        results: List of aggregated result dictionaries (output of aggregate_power_results).
        alpha_threshold: Confidence level (e.g., 0.05 for 95% CI).

    Returns:
        Dictionary with 'lower_ci' and 'upper_ci' for the most recent result or average?
        Actually, this function is usually called per configuration.
        Let's adjust signature to take a single aggregated result.
    """
    # Re-reading the requirement: compute CI for the power estimate.
    # This should be called on the aggregated result of a single configuration.
    # Let's assume the input is a single aggregated result dict.
    # If a list is passed, we compute for the last one or raise error.
    if isinstance(results, list):
        if len(results) == 0:
            return {"lower_ci": 0.0, "upper_ci": 0.0}
        result = results[-1]
    else:
        result = results

    n = result.get('total_iterations', 0)
    k = result.get('successful_replications', 0)

    if n == 0:
        return {"lower_ci": 0.0, "upper_ci": 0.0}

    if HAS_SCIPY:
        # Clopper-Pearson exact interval
        lower, upper = stats.beta.ppf([alpha_threshold / 2, 1 - alpha_threshold / 2], k, n - k + 1)
        return {"lower_ci": float(lower), "upper_ci": float(upper)}
    else:
        # Normal approximation
        p = k / n
        se = (p * (1 - p) / n) ** 0.5
        z = 1.96 # Approx for 95%
        lower = max(0.0, p - z * se)
        upper = min(1.0, p + z * se)
        return {"lower_ci": float(lower), "upper_ci": float(upper)}


def save_aggregated_results(
    aggregated_data: List[Dict[str, Any]],
    output_path: str
) -> Path:
    """
    Save the aggregated power curve results to a JSON file.

    Args:
        aggregated_data: List of aggregated result dictionaries.
        output_path: Path to the output JSON file.

    Returns:
        The Path object of the created file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    output_structure = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_configurations": len(aggregated_data)
        },
        "results": aggregated_data
    }

    with open(path, 'w') as f:
        json.dump(output_structure, f, indent=2)

    logger.info(f"Saved aggregated results to {path}")
    return path


def main():
    """
    Command-line entry point for testing the aggregator.
    """
    logging.basicConfig(level=logging.INFO)

    # Simulate some data for testing
    mock_results = [
        {"replication_success": True, "effect_size": 0.5, "p_value": 0.03},
        {"replication_success": True, "effect_size": 0.45, "p_value": 0.04},
        {"replication_success": False, "effect_size": 0.2, "p_value": 0.15},
        {"replication_success": True, "effect_size": 0.55, "p_value": 0.02},
        {"replication_success": False, "effect_size": 0.1, "p_value": 0.60},
    ]

    agg = aggregate_power_results(mock_results, sample_size=20, kernel="4s", alpha=0.05)
    print(json.dumps(agg, indent=2))

    ci = compute_confidence_intervals(agg)
    print(f"95% CI: {ci}")

    save_aggregated_results([agg], "data/aggregated/test_aggregation.json")


if __name__ == "__main__":
    main()
