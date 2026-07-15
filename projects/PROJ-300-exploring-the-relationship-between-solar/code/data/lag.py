"""
Physics-based lag calculation and application module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean_km_s: float) -> float:
    """
    Calculate the physics-based propagation lag in minutes.
    
    Formula: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw_mean_km_s / 60
    Note: The formula in T006 was L_phys = (k * 6371) / Vsw_mean / k. 
    The 'k' cancels out in the numerator/denominator if it represents the same constant, 
    but the spec implies a distance factor. Based on standard magnetospheric physics,
    the lag is Distance / Velocity. 
    Distance = K_PROPAGATION * Earth_Radius * Tail_Distance (in km).
    Velocity = Vsw (km/s).
    Result is in seconds, converted to minutes by /60.
    
    Args:
        vsw_mean_km_s: Mean solar wind speed in km/s.
        
    Returns:
        Lag in minutes.
    """
    if vsw_mean_km_s <= 0:
        raise ValueError("Vsw must be positive to calculate lag.")
    
    # Distance in km: K_PROPAGATION * Earth Radius (km) * Tail Distance (Re)
    # TAIL_DISTANCE_RE is in Earth Radii, so multiply by EARTH_RADIUS_KM
    distance_km = K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE
    
    # Time in seconds
    time_seconds = distance_km / vsw_mean_km_s
    
    # Time in minutes
    time_minutes = time_seconds / 60.0
    
    return time_minutes

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, time_col: str = 'timestamp') -> pd.DataFrame:
    """
    Shift the time series of a DataFrame by a given lag in minutes.
    This effectively aligns the data by shifting the time index forward.
    
    Args:
        df: DataFrame with a datetime index or time_col.
        lag_minutes: Lag to apply in minutes.
        time_col: Name of the timestamp column if not index.
        
    Returns:
        DataFrame with shifted timestamps.
    """
    df_shifted = df.copy()
    
    if df_shifted.index.name == time_col or (df_shifted.index.name is None and time_col not in df_shifted.columns):
        # If timestamp is index
        df_shifted.index = df_shifted.index + pd.Timedelta(minutes=lag_minutes)
    else:
        # If timestamp is a column
        df_shifted[time_col] = df_shifted[time_col] + pd.Timedelta(minutes=lag_minutes)
        
    return df_shifted
