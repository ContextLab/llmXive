"""
Sensitivity analysis module for threshold-based correlation filtering.
File: code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation
from .lag_search import find_optimal_lag


def analyze_thresholds(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: List[float] = [400, 500, 600],
    lag_window_min: int = LAG_WINDOW_MIN,
    lag_window_max: int = LAG_WINDOW_MAX,
    lag_step: int = LAG_STEP
) -> Dict[str, Dict]:
    """
    Compute correlations for different solar wind speed thresholds.

    Filters data where Vsw > threshold, then finds optimal lag and correlation.

    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with 'timestamp' and 'Vsw' columns.
    df_ey : pd.DataFrame
        DataFrame with 'timestamp' and 'Ey' columns.
    thresholds : List[float]
        List of Vsw thresholds (km/s) to test.
    lag_window_min : int
        Minimum lag to search (minutes).
    lag_window_max : int
        Maximum lag to search (minutes).
    lag_step : int
        Step size for lag search (minutes).

    Returns
    -------
    Dict[str, Dict]
        Dictionary mapping threshold string to results (optimal_lag, correlation, count).
    """
    results = {}
    for t in thresholds:
        t_str = str(t)
        # Filter Vsw data
        mask = df_vsw['Vsw'] > t
        df_vsw_filt = df_vsw[mask].copy()
        
        if len(df_vsw_filt) == 0:
            results[t_str] = {
                'threshold': t,
                'count': 0,
                'optimal_lag': None,
                'correlation': None,
                'method': 'insufficient_data'
            }
            continue

        # Align with Ey data (assuming same timestamp index or merge)
        # For simplicity, assume we merge on timestamp if not already aligned
        if 'timestamp' in df_vsw_filt.columns:
            merged = pd.merge(df_vsw_filt, df_ey, on='timestamp', how='inner')
        else:
            # If index is timestamp
            merged = pd.merge(df_vsw_filt.reset_index(), df_ey.reset_index(), on='timestamp', how='inner')
            merged.set_index('timestamp', inplace=True)

        if len(merged) < 10: # Minimum sample size for meaningful correlation
            results[t_str] = {
                'threshold': t,
                'count': len(merged),
                'optimal_lag': None,
                'correlation': None,
                'method': 'insufficient_samples'
            }
            continue

        # Find optimal lag
        try:
            optimal_lag, corr_val, _ = find_optimal_lag(
                merged['Vsw'], 
                merged['Ey'], 
                lag_window_min=lag_window_min,
                lag_window_max=lag_window_max,
                lag_step=lag_step
            )
            results[t_str] = {
                'threshold': t,
                'count': len(merged),
                'optimal_lag': optimal_lag,
                'correlation': corr_val,
                'method': 'lag_sweep'
            }
        except Exception as e:
            results[t_str] = {
                'threshold': t,
                'count': len(merged),
                'optimal_lag': None,
                'correlation': None,
                'method': 'error',
                'error': str(e)
            }

    return results


def run_sensitivity_sweep(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Run the full sensitivity sweep and return a summary DataFrame.

    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with 'timestamp' and 'Vsw' columns.
    df_ey : pd.DataFrame
        DataFrame with 'timestamp' and 'Ey' columns.
    thresholds : List[float], optional
        Defaults to [400, 500, 600].

    Returns
    -------
    pd.DataFrame
        Summary table of sensitivity results.
    """
    if thresholds is None:
        thresholds = [400, 500, 600]
    
    raw_results = analyze_thresholds(df_vsw, df_ey, thresholds=thresholds)
    
    # Convert to DataFrame
    rows = []
    for t_str, data in raw_results.items():
        rows.append({
            'threshold_km_s': data['threshold'],
            'sample_count': data['count'],
            'optimal_lag_min': data['optimal_lag'],
            'correlation_coef': data['correlation'],
            'method': data['method']
        })
    
    return pd.DataFrame(rows)
