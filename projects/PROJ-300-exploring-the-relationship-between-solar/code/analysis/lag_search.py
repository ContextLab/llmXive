"""
Lag search module to find optimal propagation lag.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift

def find_optimal_lag(df1: pd.DataFrame, df2: pd.DataFrame, min_lag: int = 30, max_lag: int = 90, step: int = 5) -> Tuple[float, float]:
    """
    Sweep the lag window and identify the optimal lag that maximizes absolute correlation.
    
    Args:
        df1: DataFrame with Vsw (index: timestamp)
        df2: DataFrame with Ey (index: timestamp)
        min_lag: Minimum lag in minutes.
        max_lag: Maximum lag in minutes.
        step: Step size in minutes.
    
    Returns:
        Tuple of (optimal_lag, max_correlation)
    """
    lags = list(range(min_lag, max_lag + 1, step))
    correlations = []
    
    for lag in lags:
        df_shifted = apply_lag_shift(df1, lag, 'Vsw')
        
        # Align
        common_idx = df_shifted.index.intersection(df2.index)
        if len(common_idx) < 10:
            correlations.append(np.nan)
            continue
        
        vsw_shifted = df_shifted.loc[common_idx, 'Vsw_lagged']
        ey = df2.loc[common_idx, 'Ey']
        
        mask = vsw_shifted.notna() & ey.notna()
        if mask.sum() < 10:
            correlations.append(np.nan)
            continue
        
        r, _, _, _ = calculate_correlation(vsw_shifted[mask], ey[mask])
        correlations.append(abs(r))
    
    valid_indices = [i for i, r in enumerate(correlations) if not np.isnan(r)]
    if not valid_indices:
        return 0.0, 0.0
    
    best_idx = max(valid_indices, key=lambda i: correlations[i])
    best_lag = lags[best_idx]
    best_corr = correlations[best_idx]
    
    return float(best_lag), float(best_corr)
