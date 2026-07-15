"""
Lag Calculation and Application Module.

Calculates physics-based lag and applies shifts to time series.

File path: code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Calculates the physics-based propagation lag (L_phys) in minutes.
    
    Formula: L_phys = (k * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw_mean
    Then converts from seconds to minutes.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        
    Returns:
        Lag in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError("Vsw mean must be positive")
    
    # Distance in km
    distance_km = EARTH_RADIUS_KM * TAIL_DISTANCE_RE
    
    # Time in seconds
    time_sec = (K_PROPAGATION * distance_km) / vsw_mean
    
    # Convert to minutes
    time_min = time_sec / 60.0
    
    return time_min

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, column: str) -> pd.DataFrame:
    """
    Applies a lag shift to a specific column in the DataFrame.
    
    Args:
        df: Input DataFrame.
        lag_minutes: Lag to apply in minutes.
        column: Column name to shift.
        
    Returns:
        DataFrame with the shifted column.
    """
    df_shifted = df.copy()
    
    # Calculate number of steps to shift based on index frequency
    # Assuming 5-minute resampling
    freq_minutes = 5
    steps = int(lag_minutes / freq_minutes)
    
    if steps > 0:
        df_shifted[column] = df_shifted[column].shift(steps)
    elif steps < 0:
        df_shifted[column] = df_shifted[column].shift(steps) # Negative shift for lead
        
    return df_shifted
