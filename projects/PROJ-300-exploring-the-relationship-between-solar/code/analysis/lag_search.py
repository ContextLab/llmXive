"""
Lag Search Module.

Identifies the optimal lag that maximizes correlation.

File path: code/analysis/lag_search.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def find_optimal_lag(
    df_sw: pd.DataFrame, 
    df_ey: pd.DataFrame,
    min_lag: int = LAG_WINDOW_MIN,
    max_lag: int = LAG_WINDOW_MAX,
    step: int = LAG_STEP
) -> Tuple[int, float, List[Dict]]:
    """
    Sweeps the lag window to find the optimal lag (L*) that maximizes absolute correlation.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: Ey DataFrame.
        min_lag: Minimum lag to search.
        max_lag: Maximum lag to search.
        step: Step size for search.
        
    Returns:
        Tuple of (optimal_lag, max_correlation, list_of_results)
    """
    lags = range(min_lag, max_lag + 1, step)
    results = []
    max_corr = -1
    optimal_lag = min_lag
    
    for lag in lags:
        # Apply lag
        df_sw_lagged = apply_lag_shift(df_sw, lag, 'Vsw')
        
        # Align
        common_idx = df_sw_lagged.index.intersection(df_ey.index)
        vsw_series = df_sw_lagged.loc[common_idx, 'Vsw']
        ey_series = df_ey.loc[common_idx, 'Ey']
        
        if len(vsw_series) < 10:
            continue
        
        # Calculate correlation
        pearson, _ = stats.pearsonr(vsw_series, ey_series)
        abs_corr = abs(pearson)
        
        results.append({
            "lag": lag,
            "pearson": pearson,
            "abs_correlation": abs_corr
        })
        
        if abs_corr > max_corr:
            max_corr = abs_corr
            optimal_lag = lag
    
    return optimal_lag, max_corr, results
