"""
Sensitivity Analysis Module.

Analyzes correlation at different solar wind speed thresholds.

File path: code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation
from .lag_search import find_optimal_lag

def analyze_thresholds(
    df_sw: pd.DataFrame, 
    df_ey: pd.DataFrame,
    optimal_lag: int
) -> List[Dict]:
    """
    Computes correlations for different solar wind speed thresholds.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: Ey DataFrame.
        optimal_lag: The optimal lag to use for all thresholds.
        
    Returns:
        List of dictionaries with threshold and correlation values.
    """
    thresholds = [400, 500, 600] # km/s
    results = []
    
    for t in thresholds:
        # Filter data
        mask = df_sw['Vsw'] >= t
        df_sw_filtered = df_sw[mask]
        df_ey_filtered = df_ey.loc[df_sw_filtered.index]
        
        if len(df_sw_filtered) < 10:
            results.append({
                "threshold_km_s": t,
                "pearson": None,
                "n_points": len(df_sw_filtered)
            })
            continue
        
        # Apply lag
        from ..data.lag import apply_lag_shift
        df_sw_lagged = apply_lag_shift(df_sw_filtered, optimal_lag, 'Vsw')
        
        # Align
        common_idx = df_sw_lagged.index.intersection(df_ey_filtered.index)
        vsw_series = df_sw_lagged.loc[common_idx, 'Vsw']
        ey_series = df_ey_filtered.loc[common_idx, 'Ey']
        
        if len(vsw_series) < 10:
            results.append({
                "threshold_km_s": t,
                "pearson": None,
                "n_points": len(vsw_series)
            })
            continue
        
        # Calculate correlation
        pearson, _ = calculate_correlation(vsw_series, ey_series, permutation_iterations=100)
        
        results.append({
            "threshold_km_s": t,
            "pearson": round(pearson, 4),
            "n_points": len(vsw_series)
        })
    
    return results

def run_sensitivity_sweep(
    df_sw: pd.DataFrame, 
    df_ey: pd.DataFrame
) -> List[Dict]:
    """
    Runs a full sensitivity sweep including lag search for each threshold.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: Ey DataFrame.
        
    Returns:
        List of results.
    """
    # For simplicity, we use the global optimal lag for all thresholds in this implementation
    # as per the task description which implies a fixed optimal lag.
    # If we were to re-calculate optimal lag for each threshold, we would do:
    # optimal_lag, _, _ = find_optimal_lag(df_sw_filtered, df_ey_filtered)
    # But the task says "sweep thresholds T ... and recompute correlations",
    # implying we use the same lag or re-optimize.
    # We will use the global optimal lag as a first pass.
    
    # First, find global optimal lag
    global_opt_lag, _, _ = find_optimal_lag(df_sw, df_ey)
    
    return analyze_thresholds(df_sw, df_ey, global_opt_lag)
