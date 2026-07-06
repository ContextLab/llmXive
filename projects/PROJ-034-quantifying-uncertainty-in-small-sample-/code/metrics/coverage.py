"""
Coverage metrics for uncertainty quantification.

This module provides logic to compare estimated confidence/credible intervals
against true parameter values to determine empirical coverage.
"""
from typing import List, Tuple, Dict, Any, Optional, Union
import numpy as np
from numpy.typing import ArrayLike


def check_coverage(
    lower_bound: float,
    upper_bound: float,
    true_value: float,
    tolerance: float = 1e-9
) -> bool:
    """
    Check if a single true parameter value falls within a given interval.

    Args:
        lower_bound: The lower edge of the confidence/credible interval.
        upper_bound: The upper edge of the confidence/credible interval.
        true_value: The ground truth parameter value.
        tolerance: A small tolerance for floating point comparison (default 1e-9).

    Returns:
        True if lower_bound <= true_value <= upper_bound, False otherwise.
    """
    return lower_bound - tolerance <= true_value <= upper_bound + tolerance


def calculate_coverage_metrics(
    intervals: List[Tuple[float, float]],
    true_values: ArrayLike
) -> Dict[str, Any]:
    """
    Calculate empirical coverage rate and average interval width for a batch of simulations.

    This function compares a list of (lower, upper) intervals against a corresponding
    list of true parameter values.

    Args:
        intervals: List of tuples (lower_bound, upper_bound) for each replication.
        true_values: Array-like of true parameter values corresponding to the intervals.

    Returns:
        A dictionary containing:
            - 'coverage_rate': Float between 0 and 1 representing the proportion of intervals covering the truth.
            - 'interval_widths': List of floats representing the width of each interval.
            - 'covered_flags': List of booleans indicating if each interval covered the truth.
            - 'mean_width': Average width of the intervals.
    """
    if len(intervals) != len(true_values):
        raise ValueError(
            f"Length mismatch: {len(intervals)} intervals vs {len(true_values)} true values."
        )

    if len(intervals) == 0:
        return {
            "coverage_rate": 0.0,
            "interval_widths": [],
            "covered_flags": [],
            "mean_width": 0.0,
            "total_evaluated": 0
        }

    true_arr = np.array(true_values)
    widths = []
    covered_flags = []

    for i, (lower, upper) in enumerate(intervals):
        width = upper - lower
        widths.append(width)

        covered = check_coverage(lower, upper, true_arr[i])
        covered_flags.append(covered)

    covered_count = sum(covered_flags)
    total_n = len(covered_flags)
    coverage_rate = covered_count / total_n if total_n > 0 else 0.0
    mean_width = float(np.mean(widths)) if widths else 0.0

    return {
        "coverage_rate": coverage_rate,
        "interval_widths": widths,
        "covered_flags": covered_flags,
        "mean_width": mean_width,
        "total_evaluated": total_n,
        "covered_count": covered_count
    }


def aggregate_coverage_by_method(
    results: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate coverage metrics across multiple simulation runs grouped by method.

    Args:
        results: List of dictionaries, each containing:
            - 'method_id': String identifier for the method (e.g., 'OLS', 'Bootstrap', 'Bayesian')
            - 'intervals': List of (lower, upper) tuples
            - 'true_values': Array of true parameter values

    Returns:
        Dictionary mapping method_id to aggregated metrics:
            - 'coverage_rate': Overall coverage rate for this method.
            - 'mean_width': Average interval width.
            - 'n_replications': Number of replications processed.
    """
    aggregated: Dict[str, Dict[str, Any]] = {}

    for run in results:
        method_id = run.get('method_id')
        if not method_id:
            continue

        if method_id not in aggregated:
            aggregated[method_id] = {
                'all_intervals': [],
                'all_true_values': [],
                'n_replications': 0
            }

        aggregated[method_id]['all_intervals'].extend(run.get('intervals', []))
        aggregated[method_id]['all_true_values'].extend(run.get('true_values', []))
        aggregated[method_id]['n_replications'] += len(run.get('intervals', []))

    final_metrics = {}
    for method_id, data in aggregated.items():
        if data['n_replications'] == 0:
            continue

        metrics = calculate_coverage_metrics(
            data['all_intervals'],
            data['all_true_values']
        )

        final_metrics[method_id] = {
            'coverage_rate': metrics['coverage_rate'],
            'mean_width': metrics['mean_width'],
            'n_replications': metrics['total_evaluated'],
            'covered_count': metrics['covered_count']
        }

    return final_metrics
