"""
Lag calculation and application module.
Implements FR-012: Physics-based lag calculation and time series shifting.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Calculate physics-based propagation lag in minutes.
    
    Formula: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM) / Vsw_mean * (1/60)
    Where Vsw is in km/s, result is in minutes.
    The factor 60 converts seconds to minutes.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
    
    Returns:
        Lag time in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError("Vsw_mean must be positive to calculate lag.")
    
    # Distance = K * Earth Radius (in km)
    # Time (seconds) = Distance / Speed (km/s)
    # Time (minutes) = Time (seconds) / 60
    distance_km = K_PROPAGATION * EARTH_RADIUS_KM
    time_minutes = (distance_km / vsw_mean) / 60.0
    
    return time_minutes

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, target_col: str) -> pd.DataFrame:
    """
    Apply a time shift to a DataFrame based on lag minutes.
    
    Args:
        df: DataFrame with 'timestamp' column.
        lag_minutes: Lag to apply in minutes (positive shifts data back in time).
        target_col: Column to shift (or all numeric columns if None).
    
    Returns:
        DataFrame with shifted timestamps.
    """
    df_shifted = df.copy()
    
    # Shift the timestamp index by the lag duration
    # If lag is positive, we shift the series "back" in time relative to the event
    # In pandas, shifting timestamps forward means the data point at t now belongs to t + lag
    # For correlation, we want to align the cause (solar wind) with the effect (tail)
    # So we shift the solar wind timestamps forward by the lag amount.
    df_shifted['timestamp'] = df_shifted['timestamp'] + pd.to_timedelta(lag_minutes, unit='m')
    
    return df_shifted
