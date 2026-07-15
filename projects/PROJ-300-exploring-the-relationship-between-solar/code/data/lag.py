"""
code/data/lag.py

Implements physics-based lag calculation and time-series shifting for solar wind
propagation analysis (FR-012).

This module calculates the time delay (L_phys) for solar wind features to travel
from the L1 point to Earth's magnetotail based on solar wind speed (Vsw), and
applies this lag to align time series data.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE


def calculate_physics_lag(vsw: float) -> float:
    """
    Calculate the physics-based propagation lag in minutes.

    Formula (FR-012):
    L_phys = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / Vsw / 60

    Where:
      - TAIL_DISTANCE_RE: Distance to magnetotail in Earth Radii (60 Re)
      - EARTH_RADIUS_KM: Radius of Earth in km (6371 km)
      - Vsw: Solar wind speed in km/s
      - 60: Conversion from seconds to minutes

    Args:
        vsw (float): Solar wind speed in km/s. Must be positive.

    Returns:
        float: Propagation lag in minutes.

    Raises:
        ValueError: If vsw is zero or negative.
    """
    if vsw <= 0:
        raise ValueError(f"Solar wind speed must be positive, got {vsw}")

    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    time_seconds = distance_km / vsw
    time_minutes = time_seconds / 60.0

    return time_minutes


def apply_lag_shift(df: pd.DataFrame, lag_minutes: float) -> pd.DataFrame:
    """
    Shift the DatetimeIndex of a DataFrame forward by a specified lag.

    This aligns upstream measurements (e.g., solar wind at L1) with downstream
    observations (e.g., magnetotail reconnection) by advancing the timestamp
    of the upstream data.

    Args:
        df (pd.DataFrame): DataFrame with a DatetimeIndex.
        lag_minutes (float): Lag to apply in minutes.

    Returns:
        pd.DataFrame: A new DataFrame with the index shifted by lag_minutes.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("Input DataFrame must have a DatetimeIndex")

    new_index = df.index + pd.Timedelta(minutes=lag_minutes)
    df_shifted = df.copy()
    df_shifted.index = new_index
    return df_shifted


def prepare_lagged_data(
    df_sw: pd.DataFrame,
    df_ey: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Calculate the physics-based lag and apply it to solar wind data.

    This function:
    1. Calculates the mean Vsw from the solar wind data (ignoring NaNs).
    2. Computes the physics-based lag (L_phys).
    3. Shifts the solar wind DataFrame forward by L_phys.
    4. Returns the shifted solar wind data, the original Ey data, and the lag value.

    Args:
        df_sw (pd.DataFrame): Solar wind data with 'Vsw' column and DatetimeIndex.
        df_ey (pd.DataFrame): THEMIS Ey data with DatetimeIndex.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, float]:
            - df_sw_shifted: Solar wind data with shifted index.
            - df_ey_out: Original Ey data (unchanged index).
            - lag: The calculated lag in minutes.

    Raises:
        ValueError: If no valid Vsw values are found to calculate lag.
    """
    # Ensure Vsw column exists
    if 'Vsw' not in df_sw.columns:
        raise ValueError("Input solar wind DataFrame must contain a 'Vsw' column")

    # Calculate mean Vsw, dropping NaNs
    vsw_mean = df_sw['Vsw'].mean()

    if pd.isna(vsw_mean) or vsw_mean == 0:
        raise ValueError("Could not calculate valid mean solar wind speed from input data")

    # Calculate physics-based lag
    lag = calculate_physics_lag(vsw_mean)

    # Apply lag shift to solar wind data
    df_sw_shifted = apply_lag_shift(df_sw, lag)

    return df_sw_shifted, df_ey, lag


def find_lag_range(
    df_sw: pd.DataFrame,
    lag_window_min: int,
    lag_window_max: int,
    lag_step: int
) -> list:
    """
    Generate a list of candidate lags for the search window.

    Args:
        df_sw (pd.DataFrame): Solar wind data (used to ensure consistency, though
                              not strictly needed for simple range generation).
        lag_window_min (int): Minimum lag in minutes.
        lag_window_max (int): Maximum lag in minutes.
        lag_step (int): Step size in minutes.

    Returns:
        list: List of candidate lag values in minutes.
    """
    return list(range(lag_window_min, lag_window_max + 1, lag_step))
