"""
Coverage metrics for predictive interval calibration.

This module computes empirical coverage rates and deviations from nominal levels.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)


def compute_coverage(
    actual: pd.Series,
    lower: np.ndarray,
    upper: np.ndarray,
    nominal_level: float
) -> float:
    """
    Compute empirical coverage rate.
    
    Coverage is the proportion of actual values that fall within the predicted interval.
    
    Args:
        actual: Actual observed values
        lower: Lower bounds of the intervals
        upper: Upper bounds of the intervals
        nominal_level: Nominal confidence level (e.g., 0.95)
        
    Returns:
        Empirical coverage rate (0.0 to 1.0)
    """
    if len(actual) != len(lower) or len(actual) != len(upper):
        raise DataValidationError(
            f"Length mismatch: actual={len(actual)}, lower={len(lower)}, upper={len(upper)}"
        )
    
    actual_values = actual.values
    
    # Count how many actual values fall within the interval
    within_interval = (actual_values >= lower) & (actual_values <= upper)
    
    # Handle NaN values
    valid_mask = ~np.isnan(actual_values) & ~np.isnan(lower) & ~np.isnan(upper)
    if np.sum(valid_mask) == 0:
        logger.warning("No valid values for coverage calculation")
        return np.nan
    
    coverage = np.sum(within_interval[valid_mask]) / np.sum(valid_mask)
    
    return float(coverage)


def compute_coverage_deviation(
    empirical_coverage: float,
    nominal_level: float
) -> float:
    """
    Compute deviation from nominal coverage level.
    
    Args:
        empirical_coverage: Observed coverage rate
        nominal_level: Expected coverage rate
        
    Returns:
        Absolute deviation
    """
    if np.isnan(empirical_coverage):
        return np.nan
    
    return abs(empirical_coverage - nominal_level)


def aggregate_coverage_results(
    coverage_results: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Aggregate coverage results across multiple series.
    
    Args:
        coverage_results: List of coverage result dictionaries
        
    Returns:
        Aggregated coverage metrics
    """
    aggregated = {}
    
    for res in coverage_results:
        coverage_metrics = res.get('coverage', {})
        for level, metrics in coverage_metrics.items():
            key = f'coverage_{level}'
            if key not in aggregated:
                aggregated[key] = []
            if not np.isnan(metrics.get('empirical_coverage', np.nan)):
                aggregated[key].append(metrics['empirical_coverage'])
    
    result = {}
    for key, values in aggregated.items():
        level = key.split('_')[1]
        result[f'avg_{key}'] = float(np.mean(values)) if values else np.nan
        result[f'std_{key}'] = float(np.std(values)) if values else np.nan
        result[f'nominal_{level}'] = float(level)
        result[f'deviation_{level}'] = result[f'avg_{key}'] - float(level) if not np.isnan(result[f'avg_{key}']) else np.nan
    
    return result


def coverage_to_dataframe(coverage_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of coverage result dictionaries to DataFrame.
    
    Args:
        coverage_results: List of dictionaries with coverage metrics
        
    Returns:
        DataFrame with coverage metrics
    """
    rows = []
    for res in coverage_results:
        base = {
            'dataset': res.get('dataset'),
            'series_id': res.get('series_id'),
            'model': res.get('model'),
            'horizon': res.get('horizon')
        }
        
        coverage_metrics = res.get('coverage', {})
        for level, metrics in coverage_metrics.items():
            row = base.copy()
            row['confidence_level'] = float(level)
            row['empirical_coverage'] = metrics.get('empirical_coverage', np.nan)
            row['deviation'] = metrics.get('deviation', np.nan)
            rows.append(row)
    
    return pd.DataFrame(rows)