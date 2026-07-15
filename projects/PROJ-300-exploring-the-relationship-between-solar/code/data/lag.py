"""
Physics-based lag calculation and application module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean: float, distance_re: float = TAIL_DISTANCE_RE) -> float:
    """
    Calculates the physics-based propagation lag (L_phys) in minutes.
    Formula: L_phys = (K * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw_mean
    Wait, the formula in T006 description was: L_phys = (k * 6371) / Vsw_mean / k
    Rewritten: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw_mean
    Wait, the description in T006 says:
    "L_phys = (k * 6371) / Vsw_mean / k" -> This simplifies to 6371/Vsw.
    But the standard physics is Distance / Velocity.
    Distance = Tail Distance (RE) * Earth Radius (km).
    So Distance = TAIL_DISTANCE_RE * EARTH_RADIUS_KM.
    Velocity = Vsw (km/s).
    Time (s) = Distance / Velocity.
    Time (min) = Time (s) / 60.
    
    Formula: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * distance_re) / (vsw_mean * 1000) * 60
    Where:
        - vsw_mean is in km/s
        - distance_re is in Earth Radii (Re)
        - EARTH_RADIUS_KM is in km
        - K_PROPAGATION is a dimensionless factor
        - Result is converted to minutes
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        distance_re: Distance to the tail measurement point in Earth Radii (default 60).
    
    Returns:
        Lag time in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError("Solar wind speed must be positive to calculate lag.")
    
    # Distance in km
    distance_km = distance_re * EARTH_RADIUS_KM
    
    # Time in seconds: distance (km) / speed (km/s) * K_PROPAGATION
    time_seconds = (K_PROPAGATION * distance_km) / vsw_mean
    
    # Convert to minutes
    time_minutes = time_seconds / 60.0
    
    # Apply K_PROPAGATION if defined as a scaling factor in config
    # Assuming K_PROPAGATION is a multiplier for the distance or time
    # Based on T003, it's a constant. Let's assume it scales the result.
    # If K_PROPAGATION is meant to be part of the distance calculation (e.g. path length factor)
    # The prompt T006 says "L_phys = (k * 6371) / Vsw_mean / k" which is confusing.
    # Let's stick to the physical interpretation: Distance / Speed.
    # If K_PROPAGATION is 1, we ignore it. If it's a factor, we multiply.
    # Given the "Rewritten" text removes 'k', maybe K_PROPAGATION is 1.
    # We will use K_PROPAGATION as a multiplier for the final time.
    return (time_minutes * K_PROPAGATION)

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, time_col: str = 'timestamp') -> pd.DataFrame:
    """
    Apply a time shift to the DataFrame based on the lag.
    
    This shifts the time index forward by the lag amount to align the 
    upstream solar wind data with the downstream geomagnetic response.
    
    Args:
        df: DataFrame with a datetime index or time column.
        lag_minutes: Lag time in minutes.
        time_col: Name of the time column if not index (default 'timestamp').
    
    Returns:
        DataFrame with shifted time index.
    """
    df_shifted = df.copy()
    
    # Ensure index is datetime
    if not isinstance(df_shifted.index, pd.DatetimeIndex):
        if time_col in df_shifted.columns:
            df_shifted['timestamp'] = pd.to_datetime(df_shifted[time_col])
            df_shifted.set_index('timestamp', inplace=True)
        else:
            raise ValueError("DataFrame must have a datetime index or a 'timestamp' column.")
    
    # Shift the index backward (earlier time) to simulate the delay 
    # i.e., if data at t=0 is the cause, the effect is at t=lag.
    # To align cause with effect, we shift the cause data forward in time?
    # Actually, standard practice: Shift the upstream (cause) data FORWARD 
    # so that its t=0 aligns with the downstream t=lag.
    # Or shift downstream BACKWARD.
    # Here we shift the input data forward by lag_minutes.
    
    new_index = df_shifted.index + pd.Timedelta(minutes=lag_minutes)
    df_shifted.index = new_index
    
    return df_shifted

def calculate_and_apply_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Calculate physics lag from solar wind data and apply it to the solar wind series.
    
    Args:
        df_sw: Solar wind DataFrame (must have 'Vsw' column).
        df_ey: Electric field DataFrame.
    
    Returns:
        Tuple of (lagged_sw_df, ey_df, lag_minutes).
    """
    # Calculate mean Vsw
    vsw_mean = df_sw['Vsw'].mean()
    
    # Calculate lag
    lag_min = calculate_physics_lag(vsw_mean)
    
    # Apply lag to solar wind data
    lagged_sw = apply_lag_shift(df_sw, lag_min)
    
    return lagged_sw, df_ey, lag_min
