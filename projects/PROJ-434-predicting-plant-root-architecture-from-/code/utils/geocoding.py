"""
Geocoding and coordinate transformation utilities.
"""
import numpy as np
from typing import Tuple, Optional, Union, List, Dict, Any
import warnings
import logging
from .exceptions import GeocodingError
import pandas as pd

def validate_coordinates(lat: Union[float, List[float]], lon: Union[float, List[float]]) -> bool:
    """Validate that coordinates are within valid ranges."""
    lat = np.array(lat) if not isinstance(lat, np.ndarray) else lat
    lon = np.array(lon) if not isinstance(lon, np.ndarray) else lon

    if np.any((lat < -90) | (lat > 90)) or np.any((lon < -180) | (lon > 180)):
        return False
    return True

def align_crs(df: pd.DataFrame, target_crs: str = "EPSG:4326") -> pd.DataFrame:
    """Ensure coordinates in the dataframe are aligned to the target CRS."""
    # Placeholder for actual CRS alignment logic using geopandas if needed
    # For now, assumes input is already in target CRS or handles simple checks
    return df

def transform_coordinates(df: pd.DataFrame, from_crs: str, to_crs: str) -> pd.DataFrame:
    """Transform coordinates from one CRS to another."""
    # Placeholder: In a real implementation, this would use geopandas or pyproj
    # raising GeocodingError if transformation fails
    if not validate_coordinates(df['lat'].values, df['lon'].values):
        raise GeocodingError("Invalid coordinates for transformation")
    return df

def get_central_meridian(utm_zone: int, northern_hemisphere: bool = True) -> float:
    """Calculate the central meridian for a given UTM zone."""
    return (utm_zone * 6) - 183

def is_valid_crs(crs_string: str) -> bool:
    """Check if a CRS string is valid (simplified check)."""
    return crs_string.startswith("EPSG:")

def get_utm_zone(lat: float, lon: float) -> int:
    """Calculate the UTM zone for a given latitude and longitude."""
    if lat < -80 or lat > 84:
        raise GeocodingError("Latitude out of UTM range")
    zone = int((lon + 180) / 6) + 1
    return zone

def get_utm_crs(lat: float, lon: float) -> str:
    """Get the UTM CRS string for a given location."""
    zone = get_utm_zone(lat, lon)
    hemisphere = "N" if lat >= 0 else "S"
    return f"EPSG:326{zone:02d}" if hemisphere == "N" else f"EPSG:327{zone:02d}"
