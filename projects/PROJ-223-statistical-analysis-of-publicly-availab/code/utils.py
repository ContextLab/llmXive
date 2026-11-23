"""
Utility functions for geospatial matching, encoding, and data manipulation.
"""
from geopy.distance import geodesic
import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def encode_severity(severity_str: str) -> int:
    """
    Encode severity string to ordinal integer.
    0: Property Damage Only
    1: Injury
    2: Fatality
    """
    if pd.isna(severity_str):
        return 0
    
    severity_str = str(severity_str).lower()
    if 'property' in severity_str or 'pdo' in severity_str:
        return 0
    elif 'injury' in severity_str:
        return 1
    elif 'fatal' in severity_str:
        return 2
    else:
        # Default to lowest severity if unknown
        return 0

def geo_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km."""
    coord1 = (lat1, lon1)
    coord2 = (lat2, lon2)
    return geodesic(coord1, coord2).km

def find_nearest_station(noaa_df: pd.DataFrame, target_lat: float, target_lon: float) -> Tuple[Optional[pd.Series], float]:
    """Find the nearest NOAA station to a target coordinate."""
    if noaa_df.empty:
        return None, float('inf')
    
    # Simple vectorized distance calculation (could be optimized with KDTree)
    noaa_df['dist'] = noaa_df.apply(
        lambda row: geo_distance(target_lat, target_lon, row['LAT'], row['LON']), 
        axis=1
    )
    
    nearest_idx = noaa_df['dist'].idxmin()
    min_dist = noaa_df.loc[nearest_idx, 'dist']
    
    return noaa_df.loc[nearest_idx], min_dist

def interpolate_weather(station_data: pd.Series, target_time: pd.Timestamp) -> Optional[dict]:
    """
    Interpolate weather data for a specific time from a station's history.
    Returns a dict with weather variables and match metadata.
    """
    # This is a simplified placeholder for the actual interpolation logic
    # In a real implementation, this would look at the station's time series
    # and perform linear interpolation between the two nearest timestamps.
    
    if 'DATE' not in station_data.index.names and 'DATE' not in station_data.index:
        # If the input is a single row summary, we can't interpolate
        # We just return the values if the time matches or is close
        return {
            'precipitation': station_data.get('precipitation', 0.0),
            'visibility': station_data.get('visibility', 10.0),
            'temperature': station_data.get('temperature', 20.0),
            'time_delta': 0
        }
    
    # Placeholder for real interpolation logic
    return {
        'precipitation': 0.0,
        'visibility': 10.0,
        'temperature': 20.0,
        'time_delta': 0
    }

def validate_geo_coordinates(lat: float, lon: float) -> bool:
    """Check if coordinates are within valid ranges (approximate US bounds)."""
    if pd.isna(lat) or pd.isna(lon):
        return False
    # Approximate US bounds
    return -125 <= lon <= -65 and 25 <= lat <= 49
