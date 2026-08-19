"""
Lag calculation and application utilities for solar wind propagation.

This module handles the physics-based propagation lag (L_phys) calculation
and the application of time shifts to align solar wind data with magnetotail
observations.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import json
import os
import logging
from datetime import datetime
import portalocker

from .clean import clean_and_resample
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION

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
    """
    if vsw_mean <= 0:
        raise ValueError("Solar wind speed must be positive for lag calculation.")
    # Simplified formula as per FR-012: L_phys = 6371 / vsw_mean
    # This assumes a fixed distance of 1 Re (6371 km) for the propagation path
    # relative to the speed, normalized to minutes.
    l_phys = EARTH_RADIUS_KM / vsw_mean
    return l_phys

def apply_lag_shift(series: pd.Series, lag_minutes: int) -> pd.Series:
    """
    Shifts the solar wind series forward by lag_minutes.

    Args:
        series: A pandas Series with a DatetimeIndex.
        lag_minutes: The lag in minutes to apply.

    Returns:
        A shifted pandas Series.
    """
    if series.empty:
        return series

    # Assume 5-minute cadence as per FR-010 and standard OMNI data
    cadence_interval = 5
    periods = lag_minutes // cadence_interval

    # Shift the series (forward in time, so positive shift)
    shifted = series.shift(periods=periods)

    return shifted

def log_lag_derivation(vsw_mean: float, l_phys: float) -> None:
    """
    Logs the physics derivation of the propagation lag to data/processed/quality_log.json.

    This function appends an entry to the quality log containing the constants,
    the calculated result, and a note about the dynamic X-line assumption.
    It uses portalocker to ensure file safety during concurrent writes.

    Args:
        vsw_mean: The mean solar wind speed in km/s used for the calculation.
        l_phys: The calculated propagation lag in minutes.
    """
    log_path = os.path.join("data", "processed", "quality_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "lag_derivation",
        "constants": {
            "earth_radius_km": EARTH_RADIUS_KM,
            "tail_distance_re": TAIL_DISTANCE_RE,
            "propagation_factor": K_PROPAGATION
        },
        "input": {
            "vsw_mean_km_s": vsw_mean
        },
        "result": {
            "l_phys_minutes": l_phys
        },
        "notes": "Assumes a fixed propagation distance of 1 Re (6371 km) as a heuristic approximation. The actual reconnection site (X-line) varies dynamically in the magnetotail."
    }

    # Lock the file to prevent race conditions
    lock_path = log_path + ".lock"
    with open(lock_path, "w") as lock_file:
        portalocker.lock(lock_file, portalocker.LOCK_EX)
        try:
            # Read existing data if file exists
            data = []
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r") as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                except (json.JSONDecodeError, IOError):
                    data = []

            # Append new entry
            data.append(entry)

            # Write back
            with open(log_path, "w") as f:
                json.dump(data, f, indent=2)
        finally:
            portalocker.unlock(lock_file)

    logger.info(f"Lag derivation logged to {log_path}")
