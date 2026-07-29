"""
Lag search module for finding optimal propagation lag.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py

Multiple-comparison correction: Uses circular block permutation test (FR-011)
Total lag candidates: (LAG_WINDOW_MAX - LAG_WINDOW_MIN) / LAG_STEP + 1
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from scipy import stats
from .correlation import calculate_correlation
from ..data.lag import apply_lag_shift
from ..config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
import logging

logger = logging.getLogger(__name__)

def find_optimal_lag(x: pd.Series, y: pd.Series, min_lag: int, max_lag: int, step: int) -> dict:
    """
    Sweep the lag window and identify optimal lag L*.
    
    Args:
        x: Solar wind time series
        y: THEMIS time series
        min_lag: Minimum lag in minutes
        max_lag: Maximum lag in minutes
        step: Lag step in minutes
        
    Returns:
        Dictionary with optimal_lag, max_correlation, lag_correlation_values
    """
    logger.info(f"Searching for optimal lag in range [{min_lag}, {max_lag}] with step {step}")
    
    lag_values = list(range(min_lag, max_lag + 1, step))
    correlation_values = []
    
    for lag in lag_values:
        # Apply lag shift
        x_lagged = apply_lag_shift(x, lag)
        
        # Calculate correlation
        corr_stats = calculate_correlation(x_lagged, y)
        correlation_values.append(abs(corr_stats['pearson']))
    
    # Find optimal lag
    max_idx = np.argmax(correlation_values)
    optimal_lag = lag_values[max_idx]
    max_correlation = correlation_values[max_idx]
    
    logger.info(f"Optimal lag found: {optimal_lag} min with correlation {max_correlation:.4f}")
    
    return {
        "optimal_lag": optimal_lag,
        "max_correlation": max_correlation,
        "lag_correlation_values": dict(zip(lag_values, correlation_values))
    }
