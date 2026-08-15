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
import portalocker

logger = logging.getLogger(__name__)

def calculate_l_phys(vsw_mean: float) -> float:
    """
    Calculates the physics-based propagation lag (L_phys) in minutes.
    
    Formula: L_phys = 6371 / vsw_mean
    Derivation: L_phys = (scale_factor * 6371) / vsw_mean / time_conversion_factor
    Where:
    - 60 Re is the nominal Earth-magnetotail distance (1 Re = 6371 km).
    - vsw_mean is the mean solar wind speed in km/s.
    Note: This uses a fixed distance as a heuristic approximation. The actual reconnection site varies dynamically.
    
    This implementation strictly follows the simplified formula required by FR-012.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        
    Returns:
        float: Lag in minutes.
    """
    if vsw_mean <= 0:
        raise ValueError(f"vsw_mean must be positive, got {vsw_mean}")
    
    # The simplified formula as per FR-012 implementation requirement:
    # L_phys = 6371 / vsw_mean
    # Note: The full derivation in the docstring explains the origin of the constants
    # (60 Re distance * 6371 km/Re) / vsw (km/s) / 60 s/min = (60 * 6371) / (vsw * 60) = 6371 / vsw
    lag_minutes = 6371.0 / vsw_mean
    
    logger.info(f"Calculated L_phys: {lag_minutes:.2f} min (vsw_mean: {vsw_mean:.2f} km/s)")
    
    return lag_minutes

def log_lag_derivation(vsw_mean: float, l_phys: float) -> None:
    """
    Logs the physics derivation of the propagation lag to data/processed/quality_log.json.
    
    This function appends an entry containing the constants, the result, and a note
    about the dynamic X-line assumption to ensure traceability to FR-012 and
    Constitution Principle VII.
    
    The function uses portalocker to ensure file safety when multiple processes
    or threads might write to the log simultaneously.
    
    Args:
        vsw_mean: Mean solar wind speed in km/s.
        l_phys: Calculated physics-based propagation lag in minutes.
    """
    log_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'quality_log.json'
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
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
    # Lock FIRST as per protocol (T006c acquires lock before T016)
    with open(log_path, 'a') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        try:
            # Read existing content
            f.seek(0)
            content = f.read()
            
            data = {"entries": []}
            if content.strip():
                try:
                    data = json.loads(content)
                    if "entries" not in data:
                        data = {"entries": []}
                except json.JSONDecodeError:
                    data = {"entries": []}
            
            # Append new entry
            data["entries"].append(entry)
            
            # Truncate and write
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
        finally:
            portalocker.unlock(f)
    
    logger.info(f"Logged lag derivation: vsw={vsw_mean:.2f} km/s -> L_phys={l_phys:.2f} min")

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shift the solar wind series forward by lag_minutes.
    
    This function applies a time shift to a pandas Series with a datetime index,
    effectively delaying the series by the specified number of minutes. This is
    used to account for the propagation time of solar wind from the L1 point
    to Earth's magnetosphere.
    
    The shift assumes a regular time cadence (default 5 minutes) and calculates
    the number of periods to shift accordingly.
    
    Args:
        series: Pandas Series with datetime index and regular cadence.
        lag_minutes: Lag in minutes to shift the series forward.
        
    Returns:
        pd.Series: Shifted series with NaN values introduced at the beginning
                   corresponding to the shift amount.
    
    Notes:
        - The shift is forward in time (positive lag), meaning data from time T
          is moved to T + lag_minutes.
        - The first `periods` values in the returned series will be NaN.
        - The index remains unchanged; only the values are shifted.
    """
    if series.empty:
        logger.warning("Attempted to shift an empty series.")
        return series
    
    # Assuming 5-minute cadence as per project standard (FR-003)
    cadence = 5
    periods = int(lag_minutes / cadence)
    
    if periods == 0:
        logger.debug("Lag is less than cadence interval, no shift applied.")
        return series
    
    shifted = series.shift(periods=periods)
    
    logger.debug(f"Applied lag shift of {periods} periods ({lag_minutes} minutes) to series of length {len(series)}")
    
    return shifted

# Backwards compatibility alias for existing imports in main.py
calculate_physics_lag = calculate_l_phys