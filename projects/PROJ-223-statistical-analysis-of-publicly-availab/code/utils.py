"""
Utility functions for geo-matching, encoding, and data handling.
"""
from geopy.distance import geodesic
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def encode_severity(value) -> Optional[str]:
    """
    Encode FARS severity codes to standard categories.
    Expected input: Integer codes (1, 2, 3) or similar.
    Returns: 'Property', 'Injury', 'Fatality', or None if invalid.
    """
    if pd.isna(value):
        return None
    
    try:
        val = int(value)
        if val == 1:
            return 'Property'
        elif val == 2:
            return 'Injury'
        elif val == 3:
            return 'Fatality'
        else:
            # NHTSA sometimes has 0 or other codes for unknown
            logger.warning(f"Unknown severity code encountered: {val}")
            return None
    except (ValueError, TypeError):
        return None

def geo_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance in km between two lat/lon points.
    """
    if any(np.isnan([lat1, lon1, lat2, lon2])):
        return np.nan
    return geodesic((lat1, lon1), (lat2, lon2)).km

def interpolate_weather(
    target_time: pd.Timestamp,
    station_data: pd.DataFrame,
    time_col: str = 'date',
    value_col: str = 'value'
) -> Optional[float]:
    """
    Linearly interpolate weather value for a specific time.
    """
    # Sort by time
    sorted_data = station_data.sort_values(by=time_col)
    
    # Find surrounding points
    before = sorted_data[sorted_data[time_col] <= target_time]
    after = sorted_data[sorted_data[time_col] >= target_time]
    
    if before.empty or after.empty:
        return None
    
    latest_before = before.iloc[-1]
    earliest_after = after.iloc[0]
    
    if latest_before[time_col] == earliest_after[time_col]:
        return latest_before[value_col]
    
    # Linear interpolation
    t0 = latest_before[time_col].timestamp()
    t1 = earliest_after[time_col].timestamp()
    t_target = target_time.timestamp()
    
    v0 = latest_before[value_col]
    v1 = earliest_after[value_col]
    
    if t1 == t0:
        return v0
        
    ratio = (t_target - t0) / (t1 - t0)
    return v0 + ratio * (v1 - v0)

def find_nearest_station(
    target_lat: float,
    target_lon: float,
    station_list: pd.DataFrame,
    lat_col: str = 'LAT',
    lon_col: str = 'LON',
    max_distance_km: float = 50.0
) -> Optional[str]:
    """
    Find the nearest NOAA station within max_distance_km.
    Returns station ID or None.
    """
    if station_list.empty:
        return None
    
    # Vectorized distance calculation for performance
    # Assuming station_list has LAT and LON columns
    if lat_col not in station_list.columns or lon_col not in station_list.columns:
        logger.error(f"Station list missing columns {lat_col} or {lon_col}")
        return None
        
    dists = station_list.apply(
        lambda row: geo_distance(target_lat, target_lon, row[lat_col], row[lon_col]),
        axis=1
    )
    
    if dists.isna().all():
        return None
        
    min_idx = dists.idxmin()
    min_dist = dists[min_idx]
    
    if min_dist > max_distance_km:
        logger.debug(f"Nearest station is too far: {min_dist:.2f} km")
        return None
        
    return station_list.loc[min_idx, 'STATION'] # Assuming 'STATION' is ID

def validate_geo_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude ranges.
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180
