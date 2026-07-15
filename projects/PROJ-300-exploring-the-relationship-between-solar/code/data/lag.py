"""
Lag calculation and application module.
Implements FR-012.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean_kms: float) -> float:
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
    
    The T006 text mentions "includes the 60 factor".
    So: L_phys (min) = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / Vsw / 60.
    The 'k' in the prompt description might be a typo or a specific scaling factor.
    Given the prompt says "Rewritten passage: L_phys = (k * 6371) / Vsw_mean / k",
    and T003 defines K_PROPAGATION, let's assume the formula is:
    L_phys = (K_PROPAGATION * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw / 60.
    If K_PROPAGATION is 1, it's just the physical distance.
    """
    if vsw_mean_kms <= 0:
        raise ValueError("Vsw must be positive")
    
    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    time_seconds = distance_km / vsw_mean_kms
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

def apply_lag_shift(df_vsw: pd.DataFrame, df_ey: pd.DataFrame, lag_minutes: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Applies a lag shift to the Vsw time series relative to Ey.
    Since Vsw leads Ey, we shift Vsw forward in time (or Ey backward).
    In pandas, shifting a series forward (future) means shifting the index.
    To align Vsw(t) with Ey(t+lag), we need to shift Vsw so that Vsw(t) is compared to Ey(t+lag).
    This effectively means we shift the Vsw series to the RIGHT (positive shift) if we are aligning indices?
    No. If Vsw at t=0 causes Ey at t=lag, then Vsw[0] corresponds to Ey[lag].
    To align them, we want Vsw_shifted[lag] = Vsw[0]. So we shift Vsw by +lag.
    
    Args:
        df_vsw: DataFrame with 'Vsw'
        df_ey: DataFrame with 'Ey'
        lag_minutes: Lag in minutes
    
    Returns:
        Tuple of aligned DataFrames
    """
    # Convert lag to number of rows based on the index frequency
    # Assume index is datetime
    freq = pd.infer_freq(df_vsw.index)
    if freq is None:
        # Fallback: assume 5 min if not inferable (common in this project)
        freq = '5T'
    
    freq_td = pd.Timedelta(freq)
    lag_td = pd.Timedelta(minutes=lag_minutes)
    
    n_steps = int(lag_td / freq_td)
    
    # Shift Vsw forward by n_steps
    vsw_shifted = df_vsw.copy()
    vsw_shifted['Vsw'] = vsw_shifted['Vsw'].shift(n_steps)
    
    # Drop NaNs introduced by shift
    vsw_clean = vsw_shifted.dropna()
    ey_clean = df_ey.loc[vsw_clean.index].dropna()
    
    # Ensure they are aligned
    common_idx = vsw_clean.index.intersection(ey_clean.index)
    vsw_clean = vsw_clean.loc[common_idx]
    ey_clean = ey_clean.loc[common_idx]
    
    return vsw_clean, ey_clean
