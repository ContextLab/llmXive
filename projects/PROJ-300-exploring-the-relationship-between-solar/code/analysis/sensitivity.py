"""
Sensitivity analysis for different thresholds.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation

def analyze_thresholds(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: List[float]
) -> Dict[float, float]:
    """
    Analyzes correlation for different solar wind speed thresholds.
    
    Args:
        df_vsw: Vsw DataFrame.
        df_ey: Ey DataFrame.
        thresholds: List of speed thresholds (km/s).
    
    Returns:
        Dictionary mapping threshold to correlation coefficient.
    """
    results = {}
    
    for thresh in thresholds:
        # Filter for high speed events
        mask = df_vsw['Vsw'] > thresh
        if mask.sum() < 10:
            results[thresh] = 0.0
            continue
        
        vsw_high = df_vsw.loc[mask, 'Vsw']
        ey_high = df_ey.loc[mask, 'Ey']
        
        r, _, _, _ = calculate_correlation(vsw_high, ey_high)
        results[thresh] = r
    
    return results

def run_sensitivity_sweep(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> Dict[str, any]:
    """
    Runs a full sensitivity sweep and returns a summary table.
    """
    if thresholds is None:
        thresholds = [400, 500, 600]
    
    table = analyze_thresholds(df_vsw, df_ey, thresholds)
    return {"sensitivity_table": table}
