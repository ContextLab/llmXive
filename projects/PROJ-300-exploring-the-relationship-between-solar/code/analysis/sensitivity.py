"""
Sensitivity analysis module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation
from .lag_search import find_optimal_lag

def analyze_thresholds(x: pd.Series, y: pd.Series, thresholds: list) -> dict:
    """
    Sweep thresholds T and recompute correlations.
    
    Args:
        x: Solar wind speed series.
        y: Ey series.
        thresholds: List of speed thresholds (km/s).
    
    Returns:
        Dictionary mapping threshold to correlation stats.
    """
    results = {}
    for t in thresholds:
        mask = x > t
        x_sub = x[mask]
        y_sub = y[mask]
        
        if len(x_sub) < 2:
            results[t] = {'pearson': np.nan, 'count': 0}
            continue
        
        # Re-calculate optimal lag for this subset? Or use global optimal?
        # Spec says "recompute correlations", implying we might need to find optimal lag again.
        # For simplicity, we use the global optimal lag or re-run find_optimal_lag.
        # Let's re-run to be accurate.
        lag_res = find_optimal_lag(x_sub, y_sub, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP)
        
        # Apply the found optimal lag
        x_shifted = apply_lag_shift(x_sub, lag_res['optimal_lag'])
        common_idx = x_shifted.index.intersection(y_sub.index)
        x_al = x_shifted.loc[common_idx]
        y_al = y_sub.loc[common_idx]
        
        corr = calculate_correlation(x_al, y_al)
        
        results[t] = {
            'pearson': corr['pearson'],
            'p_val': corr['p_val_pearson'],
            'count': len(x_al),
            'optimal_lag': lag_res['optimal_lag']
        }
    
    return results

def run_sensitivity_sweep(x: pd.Series, y: pd.Series) -> dict:
    """
    Run a full sensitivity sweep with default thresholds.
    
    Args:
        x: Solar wind speed series.
        y: Ey series.
    
    Returns:
        Sensitivity results.
    """
    thresholds = [400, 500, 600]
    return analyze_thresholds(x, y, thresholds)

# Import here to avoid circular dependency if needed in other modules
from ..data.lag import apply_lag_shift
