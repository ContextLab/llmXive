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
    
    Formula: L_phys = (K * Earth_Radius_km * Tail_Distance_RE) / Vsw_mean_km_s / 60
    (Converting seconds to minutes by dividing by 60)
    
    Args:
        vsw_mean_km_s: Mean solar wind speed in km/s.
        
    Returns:
        Lag in minutes.
    """
    if vsw_mean_km_s <= 0:
        raise ValueError("Solar wind speed must be positive.")
    
    # Distance in km = Tail_Distance_RE * EARTH_RADIUS_KM
    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    
    # Time in seconds = Distance / Speed
    time_seconds = (K_PROPAGATION * distance_km) / vsw_mean_km_s
    
    # Time in minutes
    time_minutes = time_seconds / 60.0
    
    return time_minutes

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float) -> pd.DataFrame:
    """
    Apply a time lag shift to the DataFrame by shifting the index.
    The lag is applied to the Vsw data to align it with the delayed Ey response.
    We shift the Vsw index forward by `lag_minutes` so that Vsw(t) aligns with Ey(t + lag).
    
    Args:
        df: DataFrame with 'timestamp' column.
        lag_minutes: Lag to apply in minutes.
        
    Returns:
        DataFrame with shifted timestamps.
    """
    df = df.copy()
    # Shift the timestamp column forward by the lag
    df['timestamp'] = df['timestamp'] + pd.Timedelta(minutes=lag_minutes)
    return df

def calculate_and_apply_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame, lag_minutes: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate physics lag and apply it to the solar wind data.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: THEMIS DataFrame.
        lag_minutes: Lag in minutes.
        
    Returns:
        Tuple of (shifted_df_sw, df_ey)
    """
    shifted_sw = apply_lag_shift(df_sw, lag_minutes)
    return shifted_sw, df_ey
