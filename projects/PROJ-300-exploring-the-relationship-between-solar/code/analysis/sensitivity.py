"""
Sensitivity analysis module for varying solar wind speed thresholds.
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
    thresholds: List[float],
    lag_min: int = LAG_WINDOW_MIN,
    lag_max: int = LAG_WINDOW_MAX,
    lag_step: int = LAG_STEP
) -> List[Dict[str, float]]:
    """
    Analyzes the correlation between Vsw and Ey for subsets of data exceeding
    specific solar wind speed thresholds.

    Args:
        df_vsw: DataFrame with 'timestamp' and 'Vsw' columns.
        df_ey: DataFrame with 'timestamp' and 'Ey' columns.
        thresholds: List of Vsw thresholds (km/s) to filter by.
        lag_min, lag_max, lag_step: Parameters for lag search.

    Returns:
        A list of dictionaries, each containing the threshold and the resulting
        optimal lag and correlation value.
    """
    results = []
    
    # Merge data first to ensure alignment
    # We assume df_vsw and df_ey are already cleaned/resampled
    df_merged = pd.merge_asof(
        df_vsw.sort_values('timestamp'),
        df_ey.sort_values('timestamp'),
        on='timestamp',
        direction='nearest'
    ).dropna()

    for thresh in thresholds:
        # Filter data where Vsw > threshold
        mask = df_merged['Vsw'] > thresh
        subset = df_merged[mask]

        if len(subset) < 10:
            results.append({
                "threshold_kms": float(thresh),
                "n_samples": len(subset),
                "optimal_lag_minutes": None,
                "correlation": None,
                "status": "insufficient_data"
            })
            continue

        # Run lag search on the subset
        try:
            # We need to pass the subset's Vsw and Ey series to find_optimal_lag
            # find_optimal_lag expects (df_vsw, df_ey, ...) but internally accesses columns
            # We need to adapt or create a temporary dataframe structure
            # To avoid modifying find_optimal_lag signature, we create temp DFs
            temp_vsw = subset[['timestamp', 'Vsw']].reset_index(drop=True)
            temp_ey = subset[['timestamp', 'Ey']].reset_index(drop=True)
            
            optimal_lag, corr_val = find_optimal_lag(
                temp_vsw, temp_ey, lag_min, lag_max, lag_step
            )
            
            results.append({
                "threshold_kms": float(thresh),
                "n_samples": len(subset),
                "optimal_lag_minutes": float(optimal_lag),
                "correlation": float(corr_val),
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "threshold_kms": float(thresh),
                "n_samples": len(subset),
                "optimal_lag_minutes": None,
                "correlation": None,
                "status": f"error: {str(e)}"
            })

    return results

def run_sensitivity_sweep(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> List[Dict[str, float]]:
    """
    Convenience wrapper to run sensitivity analysis with default thresholds.
    """
    if thresholds is None:
        thresholds = [400, 500, 600]
    return analyze_thresholds(df_vsw, df_ey, thresholds)
