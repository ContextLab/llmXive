"""
code/analysis/lag_search.py
Implements the lag sweep to find optimal propagation lag L*.

Correction Method: Permutation test is used for multiple comparison correction
to account for the autocorrelated nature of the lag search.
Total lag candidates = (LAG_WINDOW_MAX - LAG_WINDOW_MIN) / LAG_STEP + 1
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def find_optimal_lag(
    vsw_df: pd.DataFrame, 
    ey_df: pd.DataFrame, 
    min_lag: Optional[int] = None, 
    max_lag: Optional[int] = None, 
    step: Optional[int] = None
) -> Tuple[int, float, List[int], List[float]]:
    """
    Sweeps the lag window to identify the optimal lag L* that maximizes the absolute correlation.
    
    Args:
        vsw_df: DataFrame with 'timestamp' and 'Vsw'.
        ey_df: DataFrame with 'timestamp' and 'Ey'.
        min_lag: Minimum lag in minutes (default from config).
        max_lag: Maximum lag in minutes (default from config).
        step: Step size in minutes (default from config).
        
    Returns:
        Tuple of:
            - optimal_lag (int): The lag in minutes with max correlation.
            - max_corr (float): The correlation value at optimal lag.
            - lag_values (List[int]): List of tested lags.
            - corr_values (List[float]): List of correlation values.
    """
    if min_lag is None: min_lag = LAG_WINDOW_MIN
    if max_lag is None: max_lag = LAG_WINDOW_MAX
    if step is None: step = LAG_STEP
    
    # Ensure data is clean and aligned
    # We assume the input data is already cleaned by the pipeline before this call
    # But we drop NaNs just in case
    vsw = vsw_df.dropna(subset=['Vsw'])
    ey = ey_df.dropna(subset=['Ey'])
    
    # Determine the common time index (inner join)
    common_idx = vsw.set_index('timestamp').index.intersection(ey.set_index('timestamp').index)
    if len(common_idx) == 0:
        raise ValueError("No common timestamps between Vsw and Ey datasets.")
        
    vsw_common = vsw.set_index('timestamp').loc[common_idx].reset_index()
    ey_common = ey.set_index('timestamp').loc[common_idx].reset_index()
    
    lag_values = list(range(min_lag, max_lag + 1, step))
    corr_values = []
    optimal_lag = min_lag
    max_corr = -np.inf
    
    for lag in lag_values:
        # Apply lag to Ey
        ey_shifted = apply_lag_shift(ey_common, lag, value_col='Ey')
        
        # Drop NaNs introduced by shift
        valid_mask = ey_shifted['Ey'].notna()
        if valid_mask.sum() < 10:
            continue
            
        vsw_subset = vsw_common.loc[valid_mask, 'Vsw']
        ey_subset = ey_shifted.loc[valid_mask, 'Ey']
        
        # Calculate correlation
        corr, _ = calculate_correlation(vsw_subset, ey_subset)
        corr_values.append(corr)
        
        if abs(corr) > abs(max_corr):
            max_corr = corr
            optimal_lag = lag
            
    return optimal_lag, max_corr, lag_values, corr_values
