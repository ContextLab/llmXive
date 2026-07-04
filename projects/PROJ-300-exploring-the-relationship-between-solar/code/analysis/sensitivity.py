"""
Sensitivity analysis module for threshold-based correlation computation.
Computes correlations for Vsw thresholds T ∈ {400, 500, 600} km/s.
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
    thresholds: List[float] = [400, 500, 600]
) -> Dict[str, Dict[str, float]]:
    """
    Analyze correlation for different solar wind speed thresholds.

    Args:
        df_sw: DataFrame with 'Vsw' and 'timestamp'.
        df_ey: DataFrame with 'Ey' and 'timestamp'.
        thresholds: List of Vsw thresholds (km/s) to filter by.

    Returns:
        Dictionary mapping threshold string to correlation metrics.
    """
    results = {}
    
    # Ensure data is aligned
    if 'timestamp' in df_sw.columns and 'timestamp' in df_ey.columns:
        df_sw = df_sw.set_index('timestamp')
        df_ey = df_ey.set_index('timestamp')
        # Align on common index
        common_idx = df_sw.index.intersection(df_ey.index)
        df_sw = df_sw.loc[common_idx]
        df_ey = df_ey.loc[common_idx]

    for threshold in thresholds:
        # Filter data where Vsw >= threshold
        mask = df_sw['Vsw'] >= threshold
        vsw_filtered = df_sw.loc[mask, 'Vsw']
        ey_filtered = df_ey.loc[mask, 'Ey']

        if len(vsw_filtered) < 10:
            # Not enough data for this threshold
            results[str(threshold)] = {
                "pearson": np.nan,
                "spearman": np.nan,
                "n_points": len(vsw_filtered),
                "note": "Insufficient data"
            }
            continue

        # Calculate correlation on filtered data
        # Note: We do not re-run lag search for sensitivity; we use the global optimal lag
        # or calculate correlation directly if lag is not provided.
        # For this task, we compute correlation directly on the filtered data.
        pearson, spearman, p_val = calculate_correlation(vsw_filtered, ey_filtered)

        results[str(threshold)] = {
            "pearson": float(pearson),
            "spearman": float(spearman),
            "p_value": float(p_val),
            "n_points": int(len(vsw_filtered))
        }

    return results

def run_sensitivity_sweep(
    df_sw: pd.DataFrame,
    df_ey: pd.DataFrame,
    min_lag: int = LAG_WINDOW_MIN,
    max_lag: int = LAG_WINDOW_MAX,
    step: int = LAG_STEP,
    thresholds: List[float] = [400, 500, 600]
) -> Dict[str, Dict[str, float]]:
    """
    Run a full sensitivity sweep including lag search for each threshold.
    
    This is a more rigorous version that re-optimizes the lag for each threshold.
    
    Args:
        df_sw: DataFrame with 'Vsw' and 'timestamp'.
        df_ey: DataFrame with 'Ey' and 'timestamp'.
        min_lag: Minimum lag to search.
        max_lag: Maximum lag to search.
        step: Step size for lag search.
        thresholds: List of Vsw thresholds.
        
    Returns:
        Dictionary with sensitivity results including optimal lag per threshold.
    """
    results = {}
    
    for threshold in thresholds:
        mask = df_sw['Vsw'] >= threshold
        vsw_filtered = df_sw.loc[mask, 'Vsw']
        ey_filtered = df_ey.loc[mask, 'Ey']
        
        if len(vsw_filtered) < 20:
            results[str(threshold)] = {
                "pearson": np.nan,
                "spearman": np.nan,
                "optimal_lag": np.nan,
                "n_points": len(vsw_filtered),
                "note": "Insufficient data"
            }
            continue
        
        # Find optimal lag for this subset
        optimal_lag, corr_val, _ = find_optimal_lag(
            vsw_filtered, 
            ey_filtered, 
            min_lag=min_lag, 
            max_lag=max_lag, 
            step=step
        )
        
        # Calculate correlation at optimal lag
        pearson, spearman, p_val = calculate_correlation(vsw_filtered, ey_filtered)
        
        results[str(threshold)] = {
            "pearson": float(pearson),
            "spearman": float(spearman),
            "optimal_lag": int(optimal_lag),
            "lag_correlation": float(corr_val),
            "n_points": int(len(vsw_filtered))
        }
        
    return results
