"""
Sensitivity analysis module for varying solar wind speed thresholds.
Implements FR-007 and SC-003.
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
    lag_window_min: int = LAG_WINDOW_MIN,
    lag_window_max: int = LAG_WINDOW_MAX,
    lag_step: int = LAG_STEP
) -> Dict[str, List[Dict[str, float]]]:
    """
    Performs sensitivity analysis by filtering data based on Vsw thresholds
    and recomputing correlations and optimal lags.
    
    Args:
        df_vsw: DataFrame with 'Vsw' column
        df_ey: DataFrame with 'Ey' column
        thresholds: List of Vsw thresholds (km/s) to test (e.g., [400, 500, 600])
        lag_window_min: Minimum lag to search
        lag_window_max: Maximum lag to search
        lag_step: Step size for lag search
    
    Returns:
        Dictionary containing sensitivity results keyed by threshold.
        Structure: { "sensitivity_table": [ {"threshold": 400, "pearson": 0.5, ...}, ... ] }
    """
    results = []
    
    for thresh in thresholds:
        # Filter data: Vsw > threshold
        mask = df_vsw['Vsw'] > thresh
        if mask.sum() < 10: # Minimum sample size check
            results.append({
                "threshold": thresh,
                "pearson": None,
                "spearman": None,
                "optimal_lag": None,
                "n_samples": int(mask.sum()),
                "status": "insufficient_data"
            })
            continue

        vsw_sub = df_vsw[mask].copy()
        ey_sub = df_ey.loc[mask].copy()
        
        # Ensure alignment after filtering (resample if needed, but assume clean input)
        # Re-index to align indices
        common_idx = vsw_sub.index.intersection(ey_sub.index)
        vsw_sub = vsw_sub.loc[common_idx]
        ey_sub = ey_sub.loc[common_idx]

        if len(vsw_sub) < 10:
            results.append({
                "threshold": thresh,
                "pearson": None,
                "spearman": None,
                "optimal_lag": None,
                "n_samples": len(vsw_sub),
                "status": "insufficient_data_after_alignment"
            })
            continue

        try:
            # Find optimal lag for this subset
            opt_lag, max_corr, _ = find_optimal_lag(
                vsw_sub['Vsw'], 
                ey_sub['Ey'],
                min_lag=lag_window_min,
                max_lag=lag_window_max,
                step=lag_step
            )
            
            # Apply shift and calculate final correlation
            vsw_aligned, ey_aligned = apply_lag_shift(
                pd.DataFrame({'Vsw': vsw_sub['Vsw']}), 
                pd.DataFrame({'Ey': ey_sub['Ey']}), 
                opt_lag
            )
            
            pearson_r, spearman_r = calculate_correlation(vsw_aligned['Vsw'], ey_aligned['Ey'])
            
            results.append({
                "threshold": float(thresh),
                "pearson": float(pearson_r),
                "spearman": float(spearman_r),
                "optimal_lag": float(opt_lag),
                "n_samples": len(vsw_sub),
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "threshold": float(thresh),
                "pearson": None,
                "spearman": None,
                "optimal_lag": None,
                "n_samples": len(vsw_sub),
                "status": f"error: {str(e)}"
            })

    return {"sensitivity_table": results}

def run_sensitivity_sweep(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    min_thresh: float = 300,
    max_thresh: float = 800,
    step: float = 50
) -> List[Dict[str, float]]:
    """
    Runs a continuous sweep of thresholds.
    """
    thresholds = list(np.arange(min_thresh, max_thresh + step, step))
    return analyze_thresholds(df_vsw, df_ey, thresholds)
