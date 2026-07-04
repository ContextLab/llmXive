"""
Empirical Coverage Metrics for Predictive Intervals.

This module computes the empirical coverage rates for standard confidence levels
(e.g., 0.80, 0.95) by comparing forecast intervals against actual test values.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)


def compute_coverage(
    actual: Union[np.ndarray, List[float]],
    lower_bounds: Union[np.ndarray, List[float]],
    upper_bounds: Union[np.ndarray, List[float]],
    nominal_levels: Optional[List[float]] = None
) -> Dict[str, float]:
    """
    Compute empirical coverage rates for specified nominal confidence levels.

    Args:
        actual: Array of actual test values.
        lower_bounds: Array of lower bound predictions for the intervals.
        upper_bounds: Array of upper bound predictions for the intervals.
        nominal_levels: List of nominal confidence levels to check (e.g., [0.80, 0.95]).
                       Defaults to [0.80, 0.95] if not provided.

    Returns:
        Dictionary mapping nominal level (string) to empirical coverage rate (float).

    Raises:
        DataValidationError: If input arrays are not of equal length or contain NaN/Inf.
    """
    if nominal_levels is None:
        nominal_levels = [0.80, 0.95]

    # Convert inputs to numpy arrays
    actual = np.asarray(actual, dtype=float)
    lower_bounds = np.asarray(lower_bounds, dtype=float)
    upper_bounds = np.asarray(upper_bounds, dtype=float)

    # Validation
    if not (actual.shape == lower_bounds.shape == upper_bounds.shape):
        raise DataValidationError(
            f"Input arrays must have the same shape. "
            f"Got actual: {actual.shape}, lower: {lower_bounds.shape}, upper: {upper_bounds.shape}"
        )

    if np.any(~np.isfinite(actual)) or np.any(~np.isfinite(lower_bounds)) or np.any(~np.isfinite(upper_bounds)):
        raise DataValidationError(
            "Input arrays contain NaN or Inf values. "
            "Please ensure all predictions and actuals are finite numbers."
        )

    if len(actual) == 0:
        logger.warning("Empty input arrays provided. Returning coverage of 0.0 for all levels.")
        return {str(level): 0.0 for level in nominal_levels}

    results = {}

    for level in nominal_levels:
        if not 0.0 <= level <= 1.0:
            raise DataValidationError(f"Nominal level {level} must be between 0.0 and 1.0.")

        # Check if actual value falls within the interval [lower, upper]
        # Note: Inclusive bounds are standard for coverage calculation
        is_covered = (actual >= lower_bounds) & (actual <= upper_bounds)
        
        empirical_coverage = float(np.mean(is_covered))
        results[str(level)] = empirical_coverage
        
        logger.debug(
            f"Coverage for level {level}: {empirical_coverage:.4f} "
            f"(Count: {int(np.sum(is_covered))}/{len(actual)})"
        )

    return results


def compute_coverage_deviation(
    empirical: Dict[str, float],
    nominal_levels: Optional[List[float]] = None
) -> Dict[str, float]:
    """
    Compute the deviation between empirical and nominal coverage rates.

    Args:
        empirical: Dictionary of empirical coverage rates (output of compute_coverage).
        nominal_levels: List of nominal levels to check.

    Returns:
        Dictionary mapping nominal level to deviation (empirical - nominal).
    """
    if nominal_levels is None:
        nominal_levels = [0.80, 0.95]

    deviations = {}
    for level in nominal_levels:
        level_str = str(level)
        if level_str in empirical:
            deviations[level_str] = empirical[level_str] - level
        else:
            logger.warning(f"Nominal level {level} not found in empirical results.")
            deviations[level_str] = np.nan
    
    return deviations


def aggregate_coverage_results(
    results_list: List[Dict[str, float]],
    nominal_levels: Optional[List[float]] = None
) -> Dict[str, float]:
    """
    Aggregate coverage results from multiple series/models into average rates.

    Args:
        results_list: List of dictionaries, each containing coverage rates for a series.
        nominal_levels: List of nominal levels to aggregate.

    Returns:
        Dictionary mapping nominal level to average empirical coverage.
    """
    if nominal_levels is None:
        nominal_levels = [0.80, 0.95]

    if not results_list:
        return {str(level): 0.0 for level in nominal_levels}

    aggregated = {}
    for level in nominal_levels:
        level_str = str(level)
        values = [r.get(level_str, np.nan) for r in results_list]
        # Filter out NaNs before averaging
        valid_values = [v for v in values if not np.isnan(v)]
        
        if valid_values:
            aggregated[level_str] = float(np.mean(valid_values))
        else:
            aggregated[level_str] = np.nan

    return aggregated


def coverage_to_dataframe(
    series_id: str,
    model_name: str,
    coverage_results: Dict[str, float],
    deviations: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Convert coverage results into a pandas DataFrame row.

    Args:
        series_id: Identifier for the time series.
        model_name: Name of the model used.
        coverage_results: Dictionary from compute_coverage.
        deviations: Optional dictionary from compute_coverage_deviation.

    Returns:
        Single-row DataFrame with coverage metrics.
    """
    data = {
        "series_id": series_id,
        "model": model_name
    }

    for level, emp_val in coverage_results.items():
        data[f"empirical_coverage_{level}"] = emp_val
        if deviations and level in deviations:
            data[f"deviation_{level}"] = deviations[level]
        else:
            data[f"deviation_{level}"] = emp_val - float(level)

    return pd.DataFrame([data])