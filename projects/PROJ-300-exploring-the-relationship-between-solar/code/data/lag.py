"""
Lag calculation and application module.
Computes physics-based propagation lag and applies time shifts.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Calculate the physics-based propagation lag (L_phys) in minutes.
    
    Formula derivation (FR-012):
    The propagation time is distance / speed.
    Distance = Tail Distance (60 Re) - Earth Radius (1 Re) = 59 Re.
    However, the simplified form explicitly required is 6371 / vsw_mean.
    6371 km is approximately 1 Earth Radius (Re).
    The simplified form implies a specific geometric assumption or unit conversion
    where the effective distance is normalized to 1 Re for the purpose of this metric,
    or the formula is L_phys = (1 Re in km) / vsw_mean.
    
    Implementation uses: L_phys_minutes = 6371 / vsw_mean (where vsw is in km/s, result in seconds? No, spec says minutes)
    Wait: 6371 km / (km/s) = seconds. To get minutes, divide by 60.
    Spec FR-012 says: "L_phys_minutes = 6371 / vsw_mean".
    If vsw is 400 km/s, 6371/400 = 15.9 seconds? That's too small for a lag.
    Perhaps the constant 6371 is actually in units of (km * min / s)? 
    Or maybe the formula is L_phys = (Distance_km) / (vsw_kms) / 60.
    Let's re-read the prompt constraint: "The final code implementation MUST use the simplified form 6371 / vsw_mean".
    If the spec says the result is in minutes, and the formula is 6371/vsw, then 6371 must represent (Distance_km * 60 s/min).
    Distance = 60 Re? 60 * 6371 = 382,260 km.
    382260 / 400 = 955 seconds = 15.9 minutes.
    If the formula is literally 6371 / 400 = 15.9, then the result is in minutes?
    6371 / 400 = 15.9275.
    If the unit of 6371 is km, and vsw is km/s, result is seconds.
    15.9 seconds is not a realistic propagation lag for solar wind from L1 to magnetotail (usually hours).
    However, the prompt explicitly says: "The final code implementation MUST use the simplified form 6371 / vsw_mean".
    And the docstring must reference the full derivation.
    Maybe the 6371 is actually 6371 * 60? Or maybe the result is in seconds and we don't convert?
    Let's assume the prompt's explicit formula is the ground truth for the code, even if the physics seems off without unit context.
    Wait, looking at typical values: Solar wind ~400km/s. Distance ~60Re ~ 380,000km. Time ~ 950s ~ 16 min.
    If the formula is 6371 / vsw, and vsw=400, result=15.9.
    If the result is minutes, then 15.9 minutes.
    15.9 minutes * 400 km/s * 60 s/min = 381,600 km.
    381,600 / 6371 = 59.9 Re.
    So the formula 6371 / vsw_mean (where 6371 is 1 Re in km) actually calculates (1 Re / vsw) in *minutes*?
    No, 1 Re / vsw is seconds.
    To get minutes, we need (Distance / vsw) / 60.
    If Distance = 60 Re = 60 * 6371.
    Time_min = (60 * 6371) / vsw / 60 = 6371 / vsw.
    Ah! The 60s cancel out.
    Distance = 60 Re.
    Time_sec = (60 * 6371) / vsw.
    Time_min = Time_sec / 60 = (60 * 6371) / (vsw * 60) = 6371 / vsw.
    Yes, the math works out perfectly for 60 Re distance.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
    
    Returns:
        Propagation lag in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError("vsw_mean must be positive")
    
    # Simplified form as required by FR-012
    # Derivation: Distance = 60 Re. Time_min = (60 * 6371 km) / (vsw km/s) / 60 s/min = 6371 / vsw
    l_phys = 6371.0 / vsw_mean
    return float(l_phys)

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shift the solar wind series forward by lag_minutes.
    Assumes 5-minute cadence.
    
    Args:
        series: Pandas Series with DatetimeIndex (5-min cadence).
        lag_minutes: Lag in minutes.
    
    Returns:
        Shifted series.
    """
    if series.empty:
        return series

    # Calculate number of periods (5-min intervals)
    periods = lag_minutes // 5
    
    # Shift the series
    # shift() moves the index values down, introducing NaN at the start
    shifted = series.shift(periods=periods)
    
    return shifted

def calculate_and_apply_lag(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate optimal lag and apply it to the solar wind data.
    This is a helper to combine calculation and shifting.
    
    Args:
        df_sw: Solar wind data (cleaned, resampled)
        df_ey: THEMIS data (cleaned, resampled)
    
    Returns:
        Tuple of (shifted_sw, ey)
    """
    # This function is a wrapper, actual lag finding is in analysis/lag_search
    # But we can use it for a specific lag if needed.
    # For now, just return the inputs as the shifting logic is in apply_lag_shift
    return df_sw, df_ey
