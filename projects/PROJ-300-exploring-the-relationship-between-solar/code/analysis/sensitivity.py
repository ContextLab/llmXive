"""
Sensitivity analysis module for solar wind speed thresholds.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py
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
    thresholds: List[float] = [400.0, 500.0, 600.0],
    lag_window_min: int = LAG_WINDOW_MIN,
    lag_window_max: int = LAG_WINDOW_MAX,
    lag_step: int = LAG_STEP
) -> Dict[str, Dict[str, float]]:
    """
    Compute correlations for Vsw data filtered by different speed thresholds.

    For each threshold T, the function filters the solar wind speed (Vsw) to include
    only samples where Vsw >= T, aligns with the Ey data, finds the optimal lag
    within the specified window, and computes the correlation at that lag.

    Args:
        df_vsw: DataFrame containing 'timestamp' and 'Vsw' columns.
        df_ey: DataFrame containing 'timestamp' and 'Ey' columns.
        thresholds: List of Vsw speed thresholds (km/s) to test.
        lag_window_min: Minimum lag in minutes to search.
        lag_window_max: Maximum lag in minutes to search.
        lag_step: Step size in minutes for lag search.

    Returns:
        A dictionary mapping each threshold (as string) to a dict containing:
            - 'pearson': Pearson correlation coefficient.
            - 'spearman': Spearman correlation coefficient.
            - 'p_value': Permutation test p-value.
            - 'optimal_lag': The lag in minutes that maximized absolute correlation.
    """
    results = {}

    # Ensure timestamps are datetime objects for merging
    df_vsw = df_vsw.copy()
    df_ey = df_ey.copy()

    if not pd.api.types.is_datetime64_any_dtype(df_vsw['timestamp']):
        df_vsw['timestamp'] = pd.to_datetime(df_vsw['timestamp'])
    if not pd.api.types.is_datetime64_any_dtype(df_ey['timestamp']):
        df_ey['timestamp'] = pd.to_datetime(df_ey['timestamp'])

    for t_val in thresholds:
        # Filter Vsw data
        mask = df_vsw['Vsw'] >= t_val
        df_vsw_filtered = df_vsw[mask].copy()

        if len(df_vsw_filtered) < 10:
            # Not enough data points for meaningful correlation
            results[str(t_val)] = {
                'pearson': np.nan,
                'spearman': np.nan,
                'p_value': np.nan,
                'optimal_lag': np.nan,
                'n_samples': len(df_vsw_filtered)
            }
            continue

        # Find optimal lag for this filtered subset
        # We use the full time range of the filtered data to find the best lag
        try:
            optimal_lag, corr_val, pearson, spearman, p_val = find_optimal_lag(
                df_vsw_filtered,
                df_ey,
                lag_window_min=lag_window_min,
                lag_window_max=lag_window_max,
                lag_step=lag_step
            )
            results[str(t_val)] = {
                'pearson': float(pearson),
                'spearman': float(spearman),
                'p_value': float(p_val),
                'optimal_lag': float(optimal_lag),
                'n_samples': len(df_vsw_filtered)
            }
        except Exception as e:
            # Handle cases where correlation cannot be computed (e.g., insufficient overlap)
            results[str(t_val)] = {
                'pearson': np.nan,
                'spearman': np.nan,
                'p_value': np.nan,
                'optimal_lag': np.nan,
                'n_samples': len(df_vsw_filtered),
                'error': str(e)
            }

    return results

def run_sensitivity_sweep(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Wrapper to run the sensitivity sweep with default thresholds if none provided.

    Args:
        df_vsw: DataFrame with 'timestamp' and 'Vsw'.
        df_ey: DataFrame with 'timestamp' and 'Ey'.
        thresholds: Optional list of thresholds. Defaults to [400, 500, 600].

    Returns:
        Dictionary of results keyed by threshold string.
    """
    if thresholds is None:
        thresholds = [400.0, 500.0, 600.0]

    return analyze_thresholds(df_vsw, df_ey, thresholds=thresholds)
