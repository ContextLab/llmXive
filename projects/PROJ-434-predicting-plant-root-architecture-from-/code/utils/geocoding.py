"""
Geocoding utilities for CRS alignment and coordinate validation.
"""
import numpy as np
from typing import Tuple, Optional, Union
import warnings

try:
    import pyproj
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False
    warnings.warn("pyproj not installed. CRS operations will be limited.")

# Default CRS definitions
WGS84_CRS = "EPSG:4326"
WEB_MERCATOR_CRS = "EPSG:3857"

def validate_coordinates(
    lon: Union[float, np.ndarray],
    lat: Union[float, np.ndarray],
    min_lon: float = -180.0,
    max_lon: float = 180.0,
    min_lat: float = -90.0,
    max_lat: float = 90.0
) -> Tuple[bool, Optional[str]]:
    """
    Validate longitude and latitude coordinates.
    
    Args:
        lon: Longitude value(s).
        lat: Latitude value(s).
        min_lon: Minimum allowed longitude.
        max_lon: Maximum allowed longitude.
        min_lat: Minimum allowed latitude.
        max_lat: Maximum allowed latitude.
    
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    lon_array = np.atleast_1d(lon)
    lat_array = np.atleast_1d(lat)
    
    if len(lon_array) != len(lat_array):
        return False, "Longitude and latitude arrays must have the same length."
    
    # Check for NaN or Inf
    if np.any(np.isnan(lon_array)) or np.any(np.isnan(lat_array)):
        return False, "Coordinates contain NaN values."
    
    if np.any(np.isinf(lon_array)) or np.any(np.isinf(lat_array)):
        return False, "Coordinates contain Inf values."
    
    # Check bounds
    if np.any(lon_array < min_lon) or np.any(lon_array > max_lon):
        return False, f"Longitude out of bounds [{min_lon}, {max_lon}]."
    
    if np.any(lat_array < min_lat) or np.any(lat_array > max_lat):
        return False, f"Latitude out of bounds [{min_lat}, {max_lat}]."
    
    return True, None

def align_crs(
    source_crs: str,
    target_crs: str = WGS84_CRS
) -> Optional[pyproj.CRS]:
    """
    Get a transformation object for CRS alignment.
    
    Args:
        source_crs: Source CRS identifier (e.g., "EPSG:4326").
        target_crs: Target CRS identifier (default: WGS84).
    
    Returns:
        pyproj.Transformer object if pyproj is available, None otherwise.
    
    Raises:
        ValueError: If CRS codes are invalid.
    """
    if not HAS_PYPROJ:
        warnings.warn("pyproj not installed. Cannot perform CRS transformations.")
        return None
    
    try:
        source = pyproj.CRS(source_crs)
        target = pyproj.CRS(target_crs)
        
        return pyproj.Transformer.from_crs(
            source_crs=source,
            target_crs=target,
            always_xy=True
        )
    except pyproj.CRSError as e:
        raise ValueError(f"Invalid CRS code: {e}")

def get_central_meridian(crs: str) -> Optional[float]:
    """
    Extract the central meridian from a CRS definition.
    
    Args:
        crs: CRS identifier string.
    
    Returns:
        Central meridian in degrees, or None if not available.
    """
    if not HAS_PYPROJ:
        return None
    
    try:
        crs_obj = pyproj.CRS(crs)
        # Try to get the prime meridian
        if crs_obj.is_projected:
            proj_params = crs_obj.to_dict()
            return proj_params.get('lon_0', 0.0)
        else:
            # For geographic CRS, the central meridian is typically 0 (Greenwich)
            return 0.0
    except Exception:
        return None
