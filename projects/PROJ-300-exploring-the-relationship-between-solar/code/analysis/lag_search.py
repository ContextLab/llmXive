"""
Lag search module to find optimal propagation lag.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift

def find_optimal_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame, min_lag: int, max_lag: int, step: int) -> Tuple[float, float]:
    """
    Sweep the lag window and identify the optimal lag L* that maximizes absolute correlation.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: THEMIS DataFrame.
        min_lag: Minimum lag in minutes.
        max_lag: Maximum lag in minutes.
        step: Step size in minutes.
        
    Returns:
        Tuple of (optimal_lag, correlation_at_optimal_lag).
    """
    lags = list(range(min_lag, max_lag + 1, step))
    correlations = []
    
    for lag in lags:
        df_sw_shifted = apply_lag_shift(df_sw, lag)
        merged = pd.merge(df_sw_shifted, df_ey, on='timestamp', how='inner')
        
        if len(merged) < 2:
            correlations.append(np.nan)
            continue
        
        r, _ = calculate_correlation(merged['Vsw'], merged['Ey'], method='pearson')
        correlations.append(abs(r))
    
    best_idx = np.argmax(correlations)
    optimal_lag = lags[best_idx]
    optimal_corr = correlations[best_idx]
    
    return optimal_lag, optimal_corr
