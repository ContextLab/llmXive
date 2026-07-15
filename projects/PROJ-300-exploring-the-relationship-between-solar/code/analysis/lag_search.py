"""
Lag search module to find optimal lag.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift

def find_optimal_lag(vsw: pd.Series, ey: pd.Series, min_lag: int, max_lag: int, step: int) -> Tuple[int, float, Dict]:
    """
    Sweep the lag window to find the optimal lag L*.
    
    Args:
        vsw: Solar wind speed series
        ey: Ey series
        min_lag: Minimum lag in minutes
        max_lag: Maximum lag in minutes
        step: Step size in minutes
    
    Returns:
        Tuple of (optimal_lag, correlation_at_optimal, full_results_dict)
    """
    lags = list(range(min_lag, max_lag + 1, step))
    correlations = []
    
    for lag in lags:
        # Apply lag to Vsw (shift Vsw forward in time to align with Ey)
        # We need to align the indices.
        # Create a temporary dataframe to apply shift
        temp_df = pd.DataFrame({'Vsw': vsw, 'Ey': ey})
        temp_df_shifted = apply_lag_shift(temp_df, lag, 'Vsw')
        
        # Drop NaNs
        valid = temp_df_shifted.dropna()
        if len(valid) < 10:
            correlations.append(np.nan)
            continue
        
        corr, _ = calculate_correlation(valid['Vsw'], valid['Ey'], method='pearson')
        correlations.append(corr)
    
    # Find max absolute correlation
    valid_corr = [(l, c) for l, c in zip(lags, correlations) if not np.isnan(c)]
    if not valid_corr:
        raise ValueError("No valid correlations found in the lag window.")
    
    optimal_lag, best_corr = max(valid_corr, key=lambda x: abs(x[1]))
    
    results = {
        "lags": lags,
        "correlations": correlations,
        "optimal_lag": optimal_lag,
        "correlation_at_optimal": best_corr
    }
    
    return optimal_lag, best_corr, results
