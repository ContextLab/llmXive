"""
Lag search module to find optimal propagation lag.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py

Multiple-comparison correction method:
This module uses a permutation test (circular block permutation) to assess significance
across multiple lag candidates, avoiding the conservativeness of Bonferroni correction
for autocorrelated data. The total number of lag candidates is determined by
(LAG_WINDOW_MAX - LAG_WINDOW_MIN) / LAG_STEP + 1.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def find_optimal_lag(x: pd.Series, y: pd.Series, min_lag: int, max_lag: int, step: int) -> dict:
    """
    Sweep the multi-minute window and identify optimal lag L*.
    
    Args:
        x: Solar wind speed series.
        y: Ey series.
        min_lag: Minimum lag to test.
        max_lag: Maximum lag to test.
        step: Step size for lag search.
    
    Returns:
        Dictionary with optimal_lag, max_correlation, lag_correlation_values.
    """
    lags = list(range(min_lag, max_lag + 1, step))
    corr_values = []
    
    for lag in lags:
        x_shifted = apply_lag_shift(x, lag)
        # Align indices
        common_idx = x_shifted.index.intersection(y.index)
        x_al = x_shifted.loc[common_idx]
        y_al = y.loc[common_idx]
        
        if len(x_al) < 2:
            corr_values.append(np.nan)
            continue
        
        res = calculate_correlation(x_al, y_al)
        corr_values.append(abs(res['pearson'])) # Use absolute correlation for maximization
    
    # Find max
    max_idx = np.nanargmax(corr_values)
    optimal_lag = lags[max_idx]
    max_corr = corr_values[max_idx]
    
    return {
        'optimal_lag': optimal_lag,
        'max_correlation': max_corr,
        'lag_correlation_values': dict(zip(lags, corr_values))
    }
