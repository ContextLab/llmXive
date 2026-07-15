"""
Lag search module.
Implements FR-010: Identify optimal lag L*.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift

def find_optimal_lag(vsw: pd.Series, ey: pd.Series, min_lag: int, max_lag: int, step: int) -> Tuple[int, float]:
    """
    Sweep the lag window and identify the lag that maximizes absolute correlation.
    FR-010: Identify optimal lag L*.
    
    Args:
        vsw: Solar wind speed series.
        ey: Tail reconnection rate series.
        min_lag: Minimum lag in minutes.
        max_lag: Maximum lag in minutes.
        step: Step size in minutes.
    
    Returns:
        Tuple of (optimal_lag, max_correlation).
    """
    lags = range(min_lag, max_lag + 1, step)
    best_lag = min_lag
    best_corr = -2.0 # Initialize with a value lower than any possible correlation
    
    for lag in lags:
        # Shift vsw forward by lag
        vsw_shifted = vsw.copy()
        # We need to align the data. Since we are shifting timestamps, 
        # we must re-index or shift the values.
        # For simplicity in this search, we shift the index of vsw relative to ey.
        # However, since the data is already aligned by timestamp, we can just 
        # shift the vsw series values by the number of steps corresponding to the lag.
        
        # Calculate number of steps to shift
        # Assuming 5-minute cadence
        cadence_minutes = 5
        steps = int(lag / cadence_minutes)
        
        if steps == 0:
            continue
        
        # Shift the series
        vsw_shifted = vsw.shift(-steps) # Negative shift to look forward in time? 
        # Actually, if lag is positive, the solar wind takes time to reach the tail.
        # So the solar wind at time t causes the tail effect at time t + lag.
        # To align them, we shift the solar wind data forward by lag (so vsw[t] aligns with ey[t+lag]).
        # In pandas, shifting the index forward means shifting the values back.
        # Let's shift the vsw values by +steps (so vsw[t] moves to t+steps)
        vsw_shifted = vsw.shift(steps)
        
        # Drop NaNs introduced by shift
        valid_mask = ~vsw_shifted.isna() & ~ey.isna()
        vsw_valid = vsw_shifted[valid_mask]
        ey_valid = ey[valid_mask]
        
        if len(vsw_valid) < 10:
            continue
        
        corr, _ = calculate_correlation(vsw_valid, ey_valid, method='pearson')
        
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    
    return best_lag, best_corr
