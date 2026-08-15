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
import fcntl

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
    
    logger.info(f"Calculated L_phys: {lag_minutes:.2f} min (Distance: {distance_km} km, Vsw: {vsw_mean:.2f} km/s)")
    
    return lag_minutes

def log_lag_derivation(vsw_mean: float, l_phys: float) -> None:
    """
    Logs the physics derivation of the propagation lag to data/processed/quality_log.json.
    
    This function appends an entry containing the constants, the result, and a note
    about the dynamic X-line assumption to ensure traceability to FR-012 and
    Constitution Principle VII.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        l_phys: Calculated physics-based propagation lag in minutes.
    """
    log_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'quality_log.json'
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data or initialize with file locking for read
    data = {"entries": []}
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"entries": []}
    
    # Prepare the new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "lag_derivation",
        "constants": {
            "earth_radius_km": EARTH_RADIUS_KM,
            "tail_distance_re": TAIL_DISTANCE_RE,
            "total_distance_km": TAIL_DISTANCE_RE * EARTH_RADIUS_KM
        },
        "inputs": {
            "vsw_mean_km_s": vsw_mean
        },
        "result": {
            "l_phys_minutes": l_phys
        },
        "note": "This calculation uses a fixed distance of 60 Re as a heuristic approximation. The actual reconnection site (X-line) varies dynamically in the magnetotail."
    }
    
    # Append and write with file locking to prevent race conditions
    data["entries"].append(entry)
    
    with open(log_path, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    logger.info(f"Logged lag derivation: vsw={vsw_mean:.2f} km/s -> L_phys={l_phys:.2f} min")

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