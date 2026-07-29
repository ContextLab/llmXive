"""
Lag calculation and application module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent.parent

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Compute the physics-based propagation lag.
    
    Formula: L_phys = 6371 / vsw_mean (simplified from full derivation)
    Full derivation: L_phys = (60 * 6371) / vsw_mean / 60
    Where:
      - 60 Re = distance to magnetotail (TAIL_DISTANCE_RE)
      - 6371 km = Earth radius (EARTH_RADIUS_KM)
      - vsw_mean = mean solar wind speed in km/s
      - Division by 60 converts seconds to minutes
    
    Args:
        vsw_mean: Mean solar wind speed in km/s
        
    Returns:
        Lag in minutes
    """
    # Full derivation for logging
    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM  # 60 * 6371 km
    lag_seconds = distance_km / vsw_mean
    lag_minutes = lag_seconds / 60
    
    # Simplified formula: 6371 / vsw_mean
    lag_minutes_simplified = EARTH_RADIUS_KM / vsw_mean
    
    # Log the full derivation for traceability
    log_entry = {
        "distance_km": distance_km,
        "vsw_mean": vsw_mean,
        "lag_seconds": lag_seconds,
        "lag_minutes_full_derivation": lag_minutes,
        "lag_minutes_simplified": lag_minutes_simplified,
        "formula": "L_phys = (60 * 6371) / vsw_mean / 60"
    }
    
    logger.info(f"Physics lag calculation: {log_entry}")
    
    # Use the simplified formula as per FR-012
    return lag_minutes_simplified

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shift the solar wind series forward by lag_minutes.
    
    Args:
        series: Time series with datetime index
        lag_minutes: Lag in minutes
        
    Returns:
        Shifted series
    """
    # Determine cadence (assume 5-minute intervals based on resampling)
    cadence_interval = 5  # minutes
    
    # Calculate number of periods to shift
    periods = lag_minutes // cadence_interval
    
    # Apply shift
    shifted_series = series.shift(periods=periods)
    
    logger.info(f"Applied lag shift: {lag_minutes} minutes ({periods} periods)")
    
    return shifted_series

def calculate_and_apply_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame, vsw_mean: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate physics-based lag and apply it to solar wind data.
    
    Args:
        df_sw: Solar wind DataFrame
        df_ey: THEMIS DataFrame
        vsw_mean: Mean solar wind speed
        
    Returns:
        Tuple of (lagged_sw_df, ey_df)
    """
    lag_minutes = calculate_physics_lag(vsw_mean)
    
    # Apply lag to Vsw column
    df_sw_lagged = df_sw.copy()
    df_sw_lagged['Vsw'] = apply_lag_shift(df_sw['Vsw'], int(lag_minutes))
    
    return df_sw_lagged, df_ey
