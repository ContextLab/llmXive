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

def analyze_thresholds(df: pd.DataFrame, thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Compute correlations for different solar wind speed thresholds.
    
    Args:
        df: Merged DataFrame with 'Vsw' and 'Ey'.
        thresholds: List of Vsw thresholds in km/s.
        
    Returns:
        List of dictionaries with threshold and correlation.
    """
    results = []
    for t in thresholds:
        subset = df[df['Vsw'] >= t]
        if len(subset) < 2:
            corr = np.nan
        else:
            corr, _ = calculate_correlation(subset['Vsw'], subset['Ey'], method='pearson')
        
        results.append({
            "threshold_km_s": t,
            "n_points": len(subset),
            "correlation": float(corr) if not np.isnan(corr) else None
        })
    return results

def run_sensitivity_sweep(df_sw: pd.DataFrame, df_ey: pd.DataFrame, thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity sweep by filtering Vsw and recomputing correlations.
    """
    merged = pd.merge(df_sw, df_ey, on='timestamp', how='inner')
    return analyze_thresholds(merged, thresholds)