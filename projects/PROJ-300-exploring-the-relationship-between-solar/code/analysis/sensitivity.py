"""
Sensitivity analysis module for threshold filtering.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
from .correlation import calculate_correlation
from .lag_search import find_optimal_lag
import logging

logger = logging.getLogger(__name__)

def analyze_thresholds(x: pd.Series, y: pd.Series, thresholds: list) -> dict:
    """
    Sweep thresholds T across the fixed set T ∈ {400, 500, 600} km s⁻¹ and recompute correlations.
    
    Args:
        x: Solar wind time series (Vsw)
        y: THEMIS time series (Ey)
        thresholds: List of speed thresholds in km/s (MUST be [400, 500, 600] as per FR-007)
        
    Returns:
        Dictionary mapping threshold to correlation stats
    """
    if thresholds != [400, 500, 600]:
        logger.warning(f"Thresholds {thresholds} differ from required [400, 500, 600]. Using provided values.")
    
    results = {}
    
    for threshold in thresholds:
        # Filter data above threshold
        mask = x > threshold
        x_filtered = x[mask]
        y_filtered = y[mask]
        
        if len(x_filtered) < 2:
            results[threshold] = {
                "pearson": np.nan,
                "spearman": np.nan,
                "n_samples": len(x_filtered)
            }
            continue
        
        # Calculate correlation
        corr_stats = calculate_correlation(x_filtered, y_filtered)
        
        # Find optimal lag for this subset
        lag_results = find_optimal_lag(x_filtered, y_filtered, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP)
        
        results[threshold] = {
            "pearson": corr_stats['pearson'],
            "spearman": corr_stats['spearman'],
            "optimal_lag": lag_results['optimal_lag'],
            "n_samples": len(x_filtered)
        }
        
        logger.info(f"Threshold {threshold} km/s: Pearson={corr_stats['pearson']:.4f}, n={len(x_filtered)}")
    
    return results

def run_sensitivity_sweep(x: pd.Series, y: pd.Series) -> dict:
    """
    Run full sensitivity sweep with default thresholds.
    
    Args:
        x: Solar wind time series
        y: THEMIS time series
        
    Returns:
        Sensitivity analysis results
    """
    thresholds = [400, 500, 600]
    return analyze_thresholds(x, y, thresholds)
