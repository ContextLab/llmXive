"""
code/data/lag.py
Implements physics-based lag calculation and time-series shifting.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE


def calculate_physics_lag(vsw_mean_kms: float) -> float:
    """
    Calculate the physics-based propagation lag L_phys in minutes.
    
    Formula: L_phys = (Tail_Distance_km) / Vsw_mean_kms / 60
    where Tail_Distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    
    Args:
        vsw_mean_kms: Mean solar wind speed in km/s.
        
    Returns:
        Lag time in minutes.
    """
    tail_distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    # Time in seconds
    time_seconds = tail_distance_km / vsw_mean_kms
    # Convert to minutes
    time_minutes = time_seconds / 60.0
    return time_minutes


def apply_lag_shift(df: pd.DataFrame, lag_minutes: int, time_col: str = 'timestamp', value_col: str = 'Ey') -> pd.DataFrame:
    """
    Apply a lag shift to a time series DataFrame.
    Shifts the value_col forward by lag_minutes (simulating propagation delay).
    
    Args:
        df: DataFrame with 'timestamp' and value columns.
        lag_minutes: Lag to apply in minutes.
        time_col: Name of the timestamp column.
        value_col: Name of the value column to shift.
        
    Returns:
        DataFrame with shifted values. NaNs will appear at the beginning.
    """
    df = df.copy()
    # Calculate number of steps to shift based on the time index
    # Assuming regular cadence, we can infer step size from the first two rows
    if len(df) < 2:
        return df
        
    cadence = (df[time_col].iloc[1] - df[time_col].iloc[0]).total_seconds() / 60.0
    if cadence <= 0:
        raise ValueError("Invalid cadence detected in time series.")
        
    steps = int(round(lag_minutes / cadence))
    
    # Shift the values
    df[value_col] = df[value_col].shift(steps)
    return df


def prepare_lagged_data(vsw_df: pd.DataFrame, ey_df: pd.DataFrame, lag_minutes: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare data for correlation analysis by applying a specific lag to Ey.
    
    Args:
        vsw_df: Solar wind speed DataFrame.
        ey_df: Reconnection rate (Ey) DataFrame.
        lag_minutes: Lag to apply.
        
    Returns:
        Tuple of (Vsw_aligned, Ey_shifted) DataFrames.
    """
    # Clean and resample both to ensure alignment
    vsw_clean, ey_clean = clean_and_resample(vsw_df, ey_df)
    
    # Apply lag to Ey
    ey_shifted = apply_lag_shift(ey_clean, lag_minutes, value_col='Ey')
    
    # Drop rows where Ey is NaN due to shift
    mask = ey_shifted['Ey'].notna()
    return vsw_clean.loc[mask], ey_shifted.loc[mask]


def find_lag_range(vsw_mean_kms: float, window_min: int = 30, window_max: int = 90) -> Tuple[int, int]:
    """
    Determine the search range for lag based on physics estimate.
    Returns a range centered around L_phys.
    
    Args:
        vsw_mean_kms: Mean solar wind speed.
        window_min: Minimum lag to consider.
        window_max: Maximum lag to consider.
        
    Returns:
        Tuple of (min_lag, max_lag).
    """
    l_phys = calculate_physics_lag(vsw_mean_kms)
    # Ensure the range is within the global constraints
    start = max(window_min, int(l_phys - 15))
    end = min(window_max, int(l_phys + 15))
    
    # Fallback if physics estimate is outside bounds
    if start > end:
        start, end = window_min, window_max
        
    return start, end
