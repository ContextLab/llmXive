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
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_physics_lag(vsw_mean: float) -> float:
    """
    Compute the physics-based propagation lag (L_phys).
    
    Formula: L_phys = 6371 / vsw_mean (simplified)
    Full derivation: L_phys = (60 * 6371) / vsw_mean / 60
    Where 60 is TAIL_DISTANCE_RE (Re), 6371 is EARTH_RADIUS_KM (km), vsw_mean is km/s.
    Result is in minutes.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s
        
    Returns:
        float: Lag in minutes
    """
    # Constants
    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM  # 60 * 6371 km
    
    # Time in seconds = distance / speed
    time_seconds = distance_km / vsw_mean
    
    # Convert to minutes
    lag_minutes = time_seconds / 60.0
    
    # Log derivation for traceability
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "derivation": {
            "distance_km": distance_km,
            "vsw_mean": vsw_mean,
            "time_seconds": time_seconds,
            "lag_minutes": lag_minutes
        }
    }
    
    # Write to quality log
    log_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'quality_log.json'
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
        except:
            data = {"entries": []}
    else:
        data = {"entries": []}
        
    data["entries"].append(log_entry)
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Calculated L_phys: {lag_minutes:.2f} min (Distance: {distance_km} km, Vsw: {vsw_mean:.2f} km/s)")
    
    return lag_minutes

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shift the solar wind series forward by lag_minutes.
    
    Args:
        series: Pandas Series with datetime index
        lag_minutes: Lag in minutes
        
    Returns:
        pd.Series: Shifted series
    """
    # Assuming 5-minute cadence
    cadence = 5
    periods = int(lag_minutes / cadence)
    
    shifted = series.shift(periods=periods)
    
    logger.debug(f"Applied lag shift of {periods} periods ({lag_minutes} minutes)")
    
    return shifted
