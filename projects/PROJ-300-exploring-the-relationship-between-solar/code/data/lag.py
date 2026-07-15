"""
Physics-based lag calculation and application module.
Implements FR-012: Calculate L_phys and apply lag shifts.
File path: code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean_km_s: float) -> float:
    """
    Calculate the physics-based propagation lag in minutes.
    
    Formula: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw_mean
    Then convert from seconds to minutes (divide by 60).
    
    Args:
        vsw_mean_km_s: Mean solar wind speed in km/s.
    
    Returns:
        Lag time in minutes.
    """
    if vsw_mean_km_s <= 0:
        raise ValueError("Mean solar wind speed must be positive.")
    
    # Distance = K * R_E * Tail_Distance (in km)
    # Time (seconds) = Distance / Speed
    # Time (minutes) = Time (seconds) / 60
    
    distance_km = K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE
    time_seconds = distance_km / vsw_mean_km_s
    time_minutes = time_seconds / 60.0
    
    return time_minutes

def apply_lag_shift(df: pd.DataFrame, lag_minutes: float, target_col: str) -> pd.DataFrame:
    """
    Apply a time lag shift to a specific column in the DataFrame.
    
    Args:
        df: DataFrame with a DatetimeIndex.
        lag_minutes: Lag time in minutes.
        target_col: Name of the column to shift.
    
    Returns:
        DataFrame with the shifted column.
    """
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in DataFrame.")
    
    # Convert lag to frequency string for shift
    # We assume the index is already resampled to a regular interval (e.g., 5min)
    # Calculate number of periods to shift
    freq = pd.infer_freq(df.index)
    if freq is None:
        # Fallback if frequency cannot be inferred, assume 5min
        freq = '5min'
    
    freq_delta = pd.Timedelta(freq)
    lag_delta = pd.Timedelta(minutes=lag_minutes)
    
    # Calculate shift count (can be float, but shift() expects int, so we interpolate)
    # For simplicity in this pipeline, we shift by the nearest integer number of periods
    shift_count = int(round(lag_delta / freq_delta))
    
    if shift_count == 0:
        return df.copy()
    
    df_shifted = df.copy()
    df_shifted[target_col] = df_shifted[target_col].shift(shift_count)
    
    return df_shifted
