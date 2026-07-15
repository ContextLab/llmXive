"""
Sensitivity analysis module for solar wind speed thresholds.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation
from .lag_search import find_optimal_lag


def analyze_thresholds(
    df_vsw: pd.Series,
    df_ey: pd.Series,
    timestamps: pd.Series,
    thresholds: List[float] = [400.0, 500.0, 600.0]
) -> Dict[str, Dict[str, float]]:
    """
    Compute correlations for solar wind speed thresholds.

    Filters the data where Vsw >= threshold, finds the optimal lag for that
    subset, and calculates the correlation at that lag.

    Args:
        df_vsw: Series of solar wind speed (km/s).
        df_ey: Series of reconnection electric field (mV/m).
        timestamps: Series of timestamps for alignment.
        thresholds: List of Vsw thresholds to test (km/s).

    Returns:
        Dictionary mapping threshold (str) to results:
            {
                "400.0": {
                    "n_samples": int,
                    "optimal_lag_min": float,
                    "correlation": float,
                    "p_value": float
                },
                ...
            }
    """
    results = {}

    # Ensure inputs are aligned
    common_idx = df_vsw.index.intersection(df_ey.index)
    vsw = df_vsw.loc[common_idx]
    ey = df_ey.loc[common_idx]
    ts = timestamps.loc[common_idx]

    for t in thresholds:
        # Filter for Vsw >= threshold
        mask = vsw >= t
        vsw_sub = vsw[mask]
        ey_sub = ey[mask]
        ts_sub = ts[mask]

        n_samples = len(vsw_sub)
        if n_samples < 10:
            # Not enough data to compute meaningful correlation
            results[str(t)] = {
                "n_samples": n_samples,
                "optimal_lag_min": np.nan,
                "correlation": np.nan,
                "p_value": np.nan,
                "note": "Insufficient data points"
            }
            continue

        # Find optimal lag for this subset
        # We reuse find_optimal_lag which expects full series,
        # but we pass the subset directly.
        # Note: find_optimal_lag internally calls calculate_correlation
        # and sweeps the lag window.
        try:
            optimal_lag, corr_val, p_val = find_optimal_lag(
                vsw_sub,
                ey_sub,
                ts_sub
            )
        except Exception as e:
            # Fallback if lag search fails (e.g., constant series)
            results[str(t)] = {
                "n_samples": n_samples,
                "optimal_lag_min": np.nan,
                "correlation": np.nan,
                "p_value": np.nan,
                "note": f"Lag search failed: {str(e)}"
            }
            continue

        results[str(t)] = {
            "n_samples": n_samples,
            "optimal_lag_min": float(optimal_lag),
            "correlation": float(corr_val),
            "p_value": float(p_val)
        }

    return results


def run_sensitivity_sweep(
    df_vsw: pd.Series,
    df_ey: pd.Series,
    timestamps: pd.Series,
    thresholds: Optional[List[float]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Wrapper to run sensitivity sweep with default thresholds if none provided.

    Args:
        df_vsw: Series of solar wind speed.
        df_ey: Series of reconnection electric field.
        timestamps: Series of timestamps.
        thresholds: Optional list of thresholds. Defaults to [400, 500, 600].

    Returns:
        Dictionary of sensitivity results.
    """
    if thresholds is None:
        thresholds = [400.0, 500.0, 600.0]

    return analyze_thresholds(df_vsw, df_ey, timestamps, thresholds)
