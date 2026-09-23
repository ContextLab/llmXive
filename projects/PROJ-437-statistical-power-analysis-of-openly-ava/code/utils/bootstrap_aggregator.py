"""
Bootstrap Aggregator Module.

This module consumes the list of results per sample size from bootstrap iterations
and computes the final empirical replication rates, confidence intervals, and
aggregated statistics required for power curve generation.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def aggregate_power_results(
    bootstrap_results: List[Dict[str, Any]],
    sample_sizes: List[int],
    paradigm_id: str,
    kernel_size: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Aggregate bootstrap results per sample size to compute empirical replication rates.

    This function groups results by sample size, calculates the proportion of
    successful replications (successes / total attempts) for each size, and
    returns the aggregated power curve data.

    Args:
        bootstrap_results: List of dictionaries, each containing 'sample_size' and
                           'replication_success' (bool) or similar success metric.
        sample_sizes: List of target sample sizes tested.
        paradigm_id: Identifier for the cognitive paradigm being analyzed.
        kernel_size: Optional smoothing kernel identifier (e.g., '4mm', '8mm').

    Returns:
        Dictionary containing:
            - 'paradigm_id': str
            - 'kernel_size': str or None
            - 'sample_sizes_tested': List[int]
            - 'empirical_rates': List[float] (proportion of successes)
            - 'success_counts': List[int]
            - 'total_counts': List[int]
            - 'aggregation_timestamp': ISO timestamp string
    """
    if not bootstrap_results:
        logger.warning(f"No bootstrap results provided for {paradigm_id}. Returning empty aggregation.")
        return {
            "paradigm_id": paradigm_id,
            "kernel_size": kernel_size,
            "sample_sizes_tested": [],
            "empirical_rates": [],
            "success_counts": [],
            "total_counts": [],
            "aggregation_timestamp": "N/A",
        }

    # Group results by sample size
    grouped: Dict[int, List[bool]] = {size: [] for size in sample_sizes}

    for res in bootstrap_results:
        size = res.get("sample_size")
        if size is None or size not in grouped:
            logger.warning(f"Skipping result with unknown sample_size: {size}")
            continue

        # Determine success metric. Assumes 'replication_success' is a boolean.
        success = res.get("replication_success", False)
        if isinstance(success, bool):
            grouped[size].append(success)
        else:
            # Fallback if stored as 0/1 int
            grouped[size].append(bool(success))

    # Compute rates
    rates = []
    successes = []
    totals = []

    for size in sample_sizes:
        results_for_size = grouped[size]
        if not results_for_size:
            # No iterations ran for this size; rate is NaN or 0?
            # Spec implies we need a rate. If no data, we can't compute.
            # We'll use NaN to indicate missing data, which the model fitting should handle.
            rates.append(float("nan"))
            successes.append(0)
            totals.append(0)
        else:
            count = len(results_for_size)
            succ = sum(results_for_size)
            rates.append(succ / count)
            successes.append(succ)
            totals.append(count)

    logger.info(
        f"Aggregated {len(bootstrap_results)} results for {paradigm_id} "
        f"(kernel={kernel_size}). Computed {len(rates)} rates."
    )

    return {
        "paradigm_id": paradigm_id,
        "kernel_size": kernel_size,
        "sample_sizes_tested": sample_sizes,
        "empirical_rates": rates,
        "success_counts": successes,
        "total_counts": totals,
        "aggregation_timestamp": "N/A", # Timestamp handled by caller or generic
    }


def compute_confidence_intervals(
    aggregated_data: Dict[str, Any],
    confidence_level: float = 0.95,
) -> Dict[str, List[float]]:
    """
    Compute confidence intervals for the empirical rates using the Clopper-Pearson method.

    Args:
        aggregated_data: Output from aggregate_power_results.
        confidence_level: Confidence level (e.g., 0.95).

    Returns:
        Dictionary with keys 'lower_bound' and 'upper_bound', each a list of floats.
    """
    successes = aggregated_data.get("success_counts", [])
    totals = aggregated_data.get("total_counts", [])
    rates = aggregated_data.get("empirical_rates", [])

    if not successes or not totals:
        return {"lower_bound": [], "upper_bound": []}

    lower_bounds = []
    upper_bounds = []

    for succ, total, rate in zip(successes, totals, rates):
        if total == 0:
            lower_bounds.append(float("nan"))
            upper_bounds.append(float("nan"))
            continue

        # Use beta distribution quantiles for Clopper-Pearson
        alpha = 1.0 - confidence_level
        # scipy.stats.beta is preferred, but to minimize dependencies we use numpy approximation
        # or rely on scipy if available. Given requirements.txt includes statsmodels/scipy,
        # we can import scipy.stats.
        try:
            from scipy.stats import beta

            lower = beta.ppf(alpha / 2.0, succ, total - succ + 1) if succ > 0 else 0.0
            upper = beta.ppf(1.0 - alpha / 2.0, succ + 1, total - succ) if succ < total else 1.0
            lower_bounds.append(float(lower))
            upper_bounds.append(float(upper))
        except ImportError:
            # Fallback to normal approximation if scipy is missing (less accurate for small N)
            z = 1.96 if confidence_level == 0.95 else 1.645 # Rough approximation
            se = np.sqrt((rate * (1 - rate)) / total) if total > 0 else 0
            lower = max(0.0, rate - z * se)
            upper = min(1.0, rate + z * se)
            lower_bounds.append(float(lower))
            upper_bounds.append(float(upper))

    return {
        "lower_bound": lower_bounds,
        "upper_bound": upper_bounds,
    }


def save_aggregated_results(
    aggregated_data: Dict[str, Any],
    confidence_intervals: Dict[str, List[float]],
    output_path: Path,
) -> None:
    """
    Save the aggregated power curve results and confidence intervals to a JSON file.

    Args:
        aggregated_data: The dictionary returned by aggregate_power_results.
        confidence_intervals: The dictionary returned by compute_confidence_intervals.
        output_path: Path to the output JSON file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    final_output = {
        **aggregated_data,
        "confidence_intervals": confidence_intervals,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    logger.info(f"Saved aggregated power curve results to {output_path}")


def main() -> None:
    """
    Main entry point for the bootstrap aggregator.

    This function is intended to be called by the power_curve_generator (T022)
    to aggregate results. If run as a script, it expects arguments to simulate
    a standalone run (for testing).
    """
    parser = argparse.ArgumentParser(
        description="Aggregate bootstrap results for power curve generation."
    )
    parser.add_argument(
        "--input-json",
        type=str,
        required=True,
        help="Path to JSON file containing list of bootstrap results.",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        required=True,
        help="Path to save the aggregated results.",
    )
    parser.add_argument(
        "--paradigm",
        type=str,
        default="default",
        help="Paradigm ID for the results.",
    )
    parser.add_argument(
        "--kernel",
        type=str,
        default=None,
        help="Smoothing kernel size (e.g., '4mm').",
    )
    parser.add_argument(
        "--sample-sizes",
        type=str,
        default="10,20,30,40,50",
        help="Comma-separated list of sample sizes tested.",
    )

    args = parser.parse_args()

    # Load input results
    with open(args.input_json, "r", encoding="utf-8") as f:
        bootstrap_results = json.load(f)

    sample_sizes = [int(s) for s in args.sample_sizes.split(",")]

    # Aggregate
    agg_data = aggregate_power_results(
        bootstrap_results=bootstrap_results,
        sample_sizes=sample_sizes,
        paradigm_id=args.paradigm,
        kernel_size=args.kernel,
    )

    # Compute CIs
    cis = compute_confidence_intervals(agg_data)

    # Save
    save_aggregated_results(agg_data, cis, Path(args.output_json))


if __name__ == "__main__":
    main()