"""
Physics-based lag calculation and time series shifting module.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Calculate the physics-based propagation lag in minutes.
    
    Formula: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / (vsw_mean * 60)
    - Converts distance (km) to time (minutes) given velocity (km/s).
    - Distance = K_PROPAGATION * Earth Radius * Tail Distance (in Re).
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
    
    Returns:
        Lag time in minutes.
    
    Raises:
        ValueError: If vsw_mean is zero or negative.
    """
    if vsw_mean <= 0:
        raise ValueError("Solar wind speed must be positive to calculate lag.")
    
    # Total distance in km: K * R_earth * Tail_Dist_Re
    # Note: Tail distance is usually in Re (Earth Radii), so we multiply by R_earth
    total_distance_km = K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE
    
    # Time in seconds = distance / speed
    time_seconds = total_distance_km / vsw_mean
    
    # Convert to minutes
    time_minutes = time_seconds / 60.0
    
    return time_minutes

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, time_col: str = 'timestamp') -> pd.DataFrame:
    """
    Apply a time shift to a DataFrame based on a lag in minutes.
    
    This shifts the data forward in time (simulating propagation delay)
    by reindexing or shifting the index.
    
    Args:
        df: DataFrame with a datetime index or time_col.
        lag_minutes: Lag to apply in minutes.
        time_col: Name of the time column if not using index (default 'timestamp').
    
    Returns:
        Shifted DataFrame.
    """
    df = df.copy()
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        if time_col in df.columns:
            df = df.set_index(time_col)
            df.index = pd.to_datetime(df.index)
        else:
            raise ValueError("DataFrame must have a datetime index or specified time_col.")
    
    # Shift the index forward by lag_minutes
    # We create a new index that is shifted
    shifted_index = df.index + pd.Timedelta(minutes=lag_minutes)
    
    # Create a new DataFrame with the shifted index
    # We keep the original values but associate them with the new time
    df_shifted = df.copy()
    df_shifted.index = shifted_index
    
    return df_shifted
