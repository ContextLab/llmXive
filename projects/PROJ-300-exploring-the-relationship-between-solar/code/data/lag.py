"""
Lag calculation and application module.
Computes physics-based propagation lag and applies shifts to time series.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

# Physics constants (from config if not defined there, we define them here for clarity)
# EARTH_RADIUS_KM = 6371
# TAIL_DISTANCE_RE = 60
# K_PROPAGATION = 1.0 # Simplified

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Calculate the physics-based propagation lag.
    
    Formula: L_phys_minutes = 6371 / vsw_mean (simplified form from FR-012)
    Full derivation: (Tail Distance in km) / Vsw
    Tail Distance = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        
    Returns:
        Lag in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError("Vsw must be positive for lag calculation.")
    
    # Simplified formula as per FR-012
    # The full derivation would be: (60 * 6371) / vsw_mean / 60
    # Which simplifies to 6371 / vsw_mean
    lag_minutes = 6371.0 / vsw_mean
    
    return lag_minutes

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shift the solar wind series forward by lag_minutes.
    
    Assumes a 5-minute cadence.
    
    Args:
        series: pd.Series with DatetimeIndex.
        lag_minutes: Lag in minutes.
        
    Returns:
        Shifted series.
    """
    # Calculate number of 5-minute periods
    periods = lag_minutes // 5
    
    # Shift the series
    shifted_series = series.shift(periods=periods)
    
    return shifted_series

def calculate_and_apply_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate the physics lag and apply it to the solar wind data.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: THEMIS DataFrame.
        
    Returns:
        Tuple of (df_sw_lagged, df_ey) with aligned indices.
    """
    vsw_mean = df_sw['Vsw'].mean()
    lag_minutes = calculate_physics_lag(vsw_mean)
    
    df_sw['Vsw_lagged'] = apply_lag_shift(df_sw['Vsw'], int(lag_minutes))
    
    # Drop NaNs
    df_sw = df_sw.dropna(subset=['Vsw_lagged'])
    
    return df_sw, df_ey
