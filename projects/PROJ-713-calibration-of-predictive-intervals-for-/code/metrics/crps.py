"""
Continuous Ranked Probability Score (CRPS) metrics.

This module computes the CRPS, a proper scoring rule for probabilistic forecasts.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any

try:
    import properscoring
    HAS_PROPERSCORING = True
except ImportError:
    HAS_PROPERSCORING = False
    import warnings
    warnings.warn("properscoring not installed. CRPS will use fallback approximation.")

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)


def compute_crps(
    actual: pd.Series,
    forecasts: np.ndarray,
    intervals: Dict[str, np.ndarray]
) -> Dict[str, float]:
    """
    Compute Continuous Ranked Probability Score.
    
    CRPS measures the accuracy of probabilistic predictions.
    Lower values indicate better calibration and sharpness.
    
    Args:
        actual: Actual observed values
        forecasts: Point forecasts (mean/median)
        intervals: Dictionary of interval bounds
        
    Returns:
        Dictionary with CRPS metrics
    """
    if len(actual) != len(forecasts):
        raise DataValidationError(
            f"Length mismatch: actual={len(actual)}, forecasts={len(forecasts)}"
        )
    
    actual_values = actual.values
    
    # Use properscoring if available
    if HAS_PROPERSCORING:
        try:
            # For interval-based forecasts, we approximate the CDF
            # using the interval bounds and assume a distribution
            # We'll use the ensemble method with multiple quantile forecasts
            
            # Collect quantile forecasts from intervals
            quantiles = []
            quantile_values = []
            
            for key, values in intervals.items():
                if key.startswith('lower_'):
                    level = float(key.split('_')[1])
                    quantiles.append(1 - level)  # Lower bound is (1-alpha) quantile
                    quantile_values.append(values)
                elif key.startswith('upper_'):
                    level = float(key.split('_')[1])
                    quantiles.append(level)  # Upper bound is alpha quantile
                    quantile_values.append(values)
            
            if len(quantiles) > 0 and len(quantiles) == len(quantile_values[0]):
                # Stack quantile values
                quantile_values = np.array(quantile_values).T  # Shape: (n_samples, n_quantiles)
                quantiles = np.array(quantiles)
                
                # Use properscoring.crps_ensemble
                crps_values = properscoring.crps_ensemble(
                    actual_values,
                    quantile_values,
                    weights=None,
                    axis=1
                )
                
                mean_crps = float(np.mean(crps_values))
                std_crps = float(np.std(crps_values))
                median_crps = float(np.median(crps_values))
            else:
                # Fallback: use point forecast CRPS approximation
                # CRPS for normal distribution: 0.8 * |actual - forecast| (rough approx)
                errors = np.abs(actual_values - forecasts)
                mean_crps = float(np.mean(errors) * 0.8)
                std_crps = float(np.std(errors) * 0.8)
                median_crps = float(np.median(errors) * 0.8)
                
        except Exception as e:
            logger.warning(f"properscoring computation failed: {e}, using fallback")
            # Fallback: simple approximation using point forecast
            errors = np.abs(actual_values - forecasts)
            mean_crps = float(np.mean(errors) * 0.8)
            std_crps = float(np.std(errors) * 0.8)
            median_crps = float(np.median(errors) * 0.8)
    else:
        # Fallback without properscoring
        # Approximate CRPS using point forecast and interval width
        errors = np.abs(actual_values - forecasts)
        interval_widths = []
        
        for key, values in intervals.items():
            if key.startswith('upper_'):
                level = key.split('_')[1]
                lower_key = f'lower_{level}'
                if lower_key in intervals:
                    width = values - intervals[lower_key]
                    interval_widths.append(width)
        
        if len(interval_widths) > 0:
            avg_width = np.mean(interval_widths, axis=0)
            # CRPS approx: error + penalty for interval width
            crps_approx = errors + 0.5 * avg_width
        else:
            crps_approx = errors * 1.2  # Rough penalty factor
        
        mean_crps = float(np.mean(crps_approx))
        std_crps = float(np.std(crps_approx))
        median_crps = float(np.median(crps_approx))
    
    return {
        'mean_crps': mean_crps,
        'std_crps': std_crps,
        'median_crps': median_crps,
        'min_crps': float(np.min(crps_approx)) if HAS_PROPERSCORING or len(interval_widths) > 0 else float(np.min(errors)),
        'max_crps': float(np.max(crps_approx)) if HAS_PROPERSCORING or len(interval_widths) > 0 else float(np.max(errors))
    }


def aggregate_crps_results(crps_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate CRPS results across multiple series.
    
    Args:
        crps_results: List of CRPS result dictionaries
        
    Returns:
        Aggregated CRPS metrics
    """
    all_crps = []
    for res in crps_results:
        crps_metrics = res.get('crps', {})
        if 'mean_crps' in crps_metrics and not np.isnan(crps_metrics['mean_crps']):
            all_crps.append(crps_metrics['mean_crps'])
    
    if len(all_crps) == 0:
        return {
            'global_mean_crps': np.nan,
            'global_std_crps': np.nan,
            'global_median_crps': np.nan,
            'n_series': 0
        }
    
    return {
        'global_mean_crps': float(np.mean(all_crps)),
        'global_std_crps': float(np.std(all_crps)),
        'global_median_crps': float(np.median(all_crps)),
        'n_series': len(all_crps)
    }


def crps_to_dataframe(crps_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert list of CRPS result dictionaries to DataFrame.
    
    Args:
        crps_results: List of dictionaries with CRPS metrics
        
    Returns:
        DataFrame with CRPS metrics
    """
    rows = []
    for res in crps_results:
        row = {
            'dataset': res.get('dataset'),
            'series_id': res.get('series_id'),
            'model': res.get('model'),
            'horizon': res.get('horizon')
        }
        
        crps_metrics = res.get('crps', {})
        for key, value in crps_metrics.items():
            row[f'crps_{key}'] = value
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def compute_crps_for_series(
    actual: pd.Series,
    forecasts: np.ndarray,
    intervals: Dict[str, np.ndarray]
) -> float:
    """
    Compute CRPS for a single series (scalar result).
    
    Args:
        actual: Actual observed values
        forecasts: Point forecasts
        intervals: Dictionary of interval bounds
        
    Returns:
        Mean CRPS value
    """
    result = compute_crps(actual, forecasts, intervals)
    return result['mean_crps']
