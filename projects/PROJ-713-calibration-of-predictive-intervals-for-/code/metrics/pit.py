"""
Probability Integral Transform (PIT) metrics for predictive interval calibration.

This module computes PIT values, generates histograms, and performs statistical
tests for uniformity (Ljung-Box test) to assess distributional calibration.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any
from scipy import stats
from scipy.stats import chi2

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)


def calculate_pit(actual: np.ndarray, forecasts: np.ndarray, intervals: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Calculate Probability Integral Transform values.
    
    The PIT value for a forecast is the CDF value at the actual observation.
    For symmetric intervals, we approximate the CDF using the interval bounds.
    
    Args:
        actual: Actual observed values
        forecasts: Point forecasts
        intervals: Dictionary of interval bounds (e.g., {'lower_0.95': ..., 'upper_0.95': ...})
        
    Returns:
        Array of PIT values (should be uniform in [0, 1] for well-calibrated forecasts)
    """
    if len(actual) != len(forecasts):
        raise DataValidationError(
            f"Length mismatch: actual={len(actual)}, forecasts={len(forecasts)}"
        )
    
    # Use 0.95 confidence level intervals for PIT calculation
    lower_key = 'lower_0.95'
    upper_key = 'upper_0.95'
    
    if lower_key not in intervals or upper_key not in intervals:
        logger.warning(f"Missing interval keys. Available: {list(intervals.keys())}")
        # Fallback: use available intervals or return NaN
        return np.full(len(actual), np.nan)
    
    lower = intervals[lower_key]
    upper = intervals[upper_key]
    
    # Estimate CDF using linear interpolation between lower and upper bounds
    # Assuming symmetric distribution around forecast
    width = upper - lower
    # Handle zero-width intervals
    width = np.where(width == 0, 1e-10, width)
    
    # Position of actual within the interval
    # If actual < lower: PIT ~ 0.025 (for 95% interval)
    # If actual > upper: PIT ~ 0.975
    # If lower <= actual <= upper: linear interpolation
    
    pit_values = np.zeros(len(actual))
    
    # Below lower bound
    below_mask = actual < lower
    pit_values[below_mask] = 0.025
    
    # Above upper bound
    above_mask = actual > upper
    pit_values[above_mask] = 0.975
    
    # Within interval
    within_mask = ~below_mask & ~above_mask
    if np.any(within_mask):
        normalized_pos = (actual[within_mask] - lower[within_mask]) / width[within_mask]
        # Map [0, 1] to [0.025, 0.975]
        pit_values[within_mask] = 0.025 + normalized_pos * 0.95
    
    # Clip to [0, 1]
    pit_values = np.clip(pit_values, 0.001, 0.999)
    
    return pit_values


def generate_pit_histogram(pit_values: np.ndarray, bins: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate histogram data for PIT values.
    
    Args:
        pit_values: Array of PIT values
        bins: Number of histogram bins
        
    Returns:
        Tuple of (bin_edges, counts)
    """
    if len(pit_values) == 0:
        return np.array([]), np.array([])
    
    counts, bin_edges = np.histogram(pit_values, bins=bins, range=(0, 1))
    return bin_edges, counts


def ljung_box_test(pit_values: np.ndarray, lags: int = 10) -> Dict[str, float]:
    """
    Perform Ljung-Box test for uniformity of PIT values.
    
    The null hypothesis is that the PIT values are independently uniformly distributed.
    We test for autocorrelation in the PIT values.
    
    Args:
        pit_values: Array of PIT values
        lags: Number of lags for the test
        
    Returns:
        Dictionary with 'statistic' and 'p_value'
    """
    if len(pit_values) < lags + 10:
        logger.warning(f"Not enough data points for Ljung-Box test with {lags} lags")
        return {'statistic': np.nan, 'p_value': np.nan}
    
    # Remove NaN values
    valid_mask = ~np.isnan(pit_values)
    pit_clean = pit_values[valid_mask]
    
    if len(pit_clean) < lags + 10:
        logger.warning("Too few valid PIT values after removing NaN")
        return {'statistic': np.nan, 'p_value': np.nan}
    
    try:
        # Ljung-Box test for autocorrelation
        # Note: We test if PIT values are autocorrelated (should not be if uniform)
        stat, p_value = stats.ljungbox(pit_clean, lags=[lags], return_df=False)
        
        return {
            'statistic': float(stat[0]),
            'p_value': float(p_value[0])
        }
    except Exception as e:
        logger.warning(f"Ljung-Box test failed: {e}")
        return {'statistic': np.nan, 'p_value': np.nan}


def compute_pit_metrics(
    actual: pd.Series,
    forecasts: np.ndarray,
    intervals: Dict[str, np.ndarray],
    confidence_levels: List[float] = [0.80, 0.95]
) -> Dict[str, float]:
    """
    Compute comprehensive PIT metrics for a series.
    
    Args:
        actual: Actual observed values
        forecasts: Point forecasts
        intervals: Dictionary of interval bounds
        confidence_levels: Confidence levels to consider
        
    Returns:
        Dictionary with PIT metrics
    """
    pit_values = calculate_pit(actual.values, forecasts, intervals)
    
    # Remove NaN for metrics calculation
    pit_clean = pit_values[~np.isnan(pit_values)]
    
    if len(pit_clean) == 0:
        return {
            'mean_pit': np.nan,
            'std_pit': np.nan,
            'uniformity_p_value': np.nan,
            'histogram_bins': np.nan,
            'histogram_counts': np.nan
        }
    
    # Mean should be close to 0.5 for uniform distribution
    mean_pit = float(np.mean(pit_clean))
    std_pit = float(np.std(pit_clean))
    
    # Ljung-Box test for uniformity
    lb_result = ljung_box_test(pit_clean)
    
    # Histogram (for visualization, return counts)
    _, hist_counts = generate_pit_histogram(pit_clean, bins=20)
    
    return {
        'mean_pit': mean_pit,
        'std_pit': std_pit,
        'uniformity_p_value': lb_result['p_value'],
        'uniformity_statistic': lb_result['statistic'],
        'histogram_bins': 20,
        'histogram_counts': list(hist_counts)  # Convert to list for CSV serialization
    }


def pit_metrics_to_dataframe(pit_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of PIT result dictionaries to DataFrame.
    
    Args:
        pit_results: List of dictionaries with PIT metrics
        
    Returns:
        DataFrame with PIT metrics
    """
    rows = []
    for res in pit_results:
        row = {
            'dataset': res.get('dataset'),
            'series_id': res.get('series_id'),
            'model': res.get('model'),
            'horizon': res.get('horizon')
        }
        
        pit_metrics = res.get('pit', {})
        for key, value in pit_metrics.items():
            if isinstance(value, list):
                # Convert list to string for CSV
                row[f'pit_{key}'] = ';'.join(map(str, value))
            else:
                row[f'pit_{key}'] = value
        
        rows.append(row)
    
    return pd.DataFrame(rows)
