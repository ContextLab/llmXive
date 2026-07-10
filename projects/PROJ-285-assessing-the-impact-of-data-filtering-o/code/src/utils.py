"""
Coordinate matching utilities for gravitational lens detection analysis.

Provides functions to match Right Ascension (RA) and Declination (Dec)
coordinates between different catalogs with a specified angular tolerance.
"""
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Conversion constants
ARCSEC_TO_DEG = 1.0 / 3600.0
DEG_TO_RADIANS = np.pi / 180.0


def angular_distance(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """
    Calculate the angular distance between two celestial coordinates in degrees.
    
    Uses the Haversine formula for accurate small-angle calculations on a sphere.
    
    Args:
        ra1: Right Ascension of point 1 (degrees)
        dec1: Declination of point 1 (degrees)
        ra2: Right Ascension of point 2 (degrees)
        dec2: Declination of point 2 (degrees)
        
    Returns:
        Angular distance in degrees
    """
    # Convert to radians
    ra1_rad = ra1 * DEG_TO_RADIANS
    dec1_rad = dec1 * DEG_TO_RADIANS
    ra2_rad = ra2 * DEG_TO_RADIANS
    dec2_rad = dec2 * DEG_TO_RADIANS
    
    # Haversine formula
    d_ra = ra2_rad - ra1_rad
    d_dec = dec2_rad - dec1_rad
    
    a = np.sin(d_dec / 2.0)**2 + np.cos(dec1_rad) * np.cos(dec2_rad) * np.sin(d_ra / 2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    
    # Convert back to degrees
    return c * (180.0 / np.pi)


def match_coordinates(
    catalog_a: np.ndarray,
    catalog_b: np.ndarray,
    tolerance_arcsec: float = 1.0,
    col_ra_a: str = 'RA',
    col_dec_a: str = 'Dec',
    col_ra_b: str = 'RA',
    col_dec_b: str = 'Dec'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Match coordinates between two catalogs within a specified angular tolerance.
    
    This function performs a nearest-neighbor search to find matches between
    coordinates in catalog_a and catalog_b. For each row in catalog_a, it finds
    the closest row in catalog_b and checks if the angular distance is within
    the specified tolerance.
    
    Args:
        catalog_a: 2D numpy array or pandas DataFrame for the first catalog
        catalog_b: 2D numpy array or pandas DataFrame for the second catalog
        tolerance_arcsec: Matching tolerance in arcseconds (default: 1.0)
        col_ra_a: Column name for RA in catalog_a (default: 'RA')
        col_dec_a: Column name for Dec in catalog_a (default: 'Dec')
        col_ra_b: Column name for RA in catalog_b (default: 'RA')
        col_dec_b: Column name for Dec in catalog_b (default: 'Dec')
        
    Returns:
        Tuple of (indices_a, indices_b, distances_degrees):
            - indices_a: Array of indices from catalog_a that have matches
            - indices_b: Array of indices from catalog_b that are matched
            - distances_degrees: Array of angular distances for matched pairs (in degrees)
    """
    # Convert tolerance to degrees
    tolerance_deg = tolerance_arcsec * ARCSEC_TO_DEG
    
    # Extract coordinates
    if hasattr(catalog_a, 'columns'):
        # Handle pandas DataFrame
        ra_a = catalog_a[col_ra_a].values
        dec_a = catalog_a[col_dec_a].values
    else:
        # Assume numpy array or list
        ra_a = np.asarray(catalog_a)[:, 0] if catalog_a.ndim > 1 else np.asarray(catalog_a)
        dec_a = np.asarray(catalog_a)[:, 1] if catalog_a.ndim > 1 else np.asarray(catalog_a)
        
    if hasattr(catalog_b, 'columns'):
        # Handle pandas DataFrame
        ra_b = catalog_b[col_ra_b].values
        dec_b = catalog_b[col_dec_b].values
    else:
        # Assume numpy array or list
        ra_b = np.asarray(catalog_b)[:, 0] if catalog_b.ndim > 1 else np.asarray(catalog_b)
        dec_b = np.asarray(catalog_b)[:, 1] if catalog_b.ndim > 1 else np.asarray(catalog_b)
    
    # Handle empty catalogs
    if len(ra_a) == 0 or len(ra_b) == 0:
        logger.warning("One of the catalogs is empty. No matches possible.")
        return np.array([]), np.array([]), np.array([])
    
    # Initialize result arrays
    matches_a = []
    matches_b = []
    distances = []
    
    # For small catalogs, use brute force
    if len(ra_a) * len(ra_b) < 10_000_000:  # ~10M comparisons threshold
        for i in range(len(ra_a)):
            # Calculate distances to all points in catalog_b
            dists = angular_distance(
                ra_a[i], dec_a[i],
                ra_b, dec_b
            )
            
            # Find the minimum distance
            min_idx = np.argmin(dists)
            min_dist = dists[min_idx]
            
            # Check if within tolerance
            if min_dist <= tolerance_deg:
                matches_a.append(i)
                matches_b.append(min_idx)
                distances.append(min_dist)
    else:
        # For larger catalogs, use a more efficient approach with vectorization
        # Convert to radians for efficient calculation
        ra_a_rad = ra_a * DEG_TO_RADIANS
        dec_a_rad = dec_a * DEG_TO_RADIANS
        ra_b_rad = ra_b * DEG_TO_RADIANS
        dec_b_rad = dec_b * DEG_TO_RADIANS
        
        # Calculate cosine of angular distance using dot product
        # cos(d) = sin(dec1)sin(dec2) + cos(dec1)cos(dec2)cos(ra1-ra2)
        # This is more efficient for vectorized operations
        
        # Precompute trigonometric values
        sin_dec_a = np.sin(dec_a_rad)
        cos_dec_a = np.cos(dec_a_rad)
        sin_dec_b = np.sin(dec_b_rad)
        cos_dec_b = np.cos(dec_b_rad)
        
        for i in range(len(ra_a)):
            # Calculate cos(d) for all points in catalog_b
            cos_d = (
                sin_dec_a[i] * sin_dec_b +
                cos_dec_a[i] * cos_dec_b * np.cos(ra_a_rad[i] - ra_b_rad)
            )
            
            # Handle numerical errors
            cos_d = np.clip(cos_d, -1.0, 1.0)
            
            # Calculate angular distance
            dists = np.arccos(cos_d)
            
            # Find the minimum distance
            min_idx = np.argmin(dists)
            min_dist = dists[min_idx]
            
            # Check if within tolerance
            if min_dist <= tolerance_deg * DEG_TO_RADIANS:
                matches_a.append(i)
                matches_b.append(min_idx)
                distances.append(min_dist * (180.0 / np.pi))
    
    # Convert to numpy arrays
    indices_a = np.array(matches_a)
    indices_b = np.array(matches_b)
    distances_deg = np.array(distances)
    
    logger.info(f"Found {len(indices_a)} matches within {tolerance_arcsec} arcsec tolerance")
    
    return indices_a, indices_b, distances_deg


def find_matches_in_catalog(
    query_coords: dict,
    target_catalog,
    tolerance_arcsec: float = 1.0
) -> Optional[int]:
    """
    Find the index of the closest match for a single coordinate in a target catalog.
    
    Args:
        query_coords: Dictionary with 'RA' and 'Dec' keys
        target_catalog: Catalog to search (pandas DataFrame or numpy array)
        tolerance_arcsec: Matching tolerance in arcseconds (default: 1.0)
        
    Returns:
        Index of the matching row in target_catalog, or None if no match found
    """
    if not query_coords:
        logger.error("Query coordinates are empty")
        return None
        
    ra_q = query_coords.get('RA')
    dec_q = query_coords.get('Dec')
    
    if ra_q is None or dec_q is None:
        logger.error(f"Missing RA or Dec in query coordinates: {query_coords}")
        return None
        
    if hasattr(target_catalog, 'columns'):
        # Handle pandas DataFrame
        ra_t = target_catalog['RA'].values
        dec_t = target_catalog['Dec'].values
    else:
        # Assume numpy array
        ra_t = np.asarray(target_catalog)[:, 0]
        dec_t = np.asarray(target_catalog)[:, 1]
        
    if len(ra_t) == 0:
        logger.warning("Target catalog is empty")
        return None
        
    # Calculate distances
    dists = angular_distance(ra_q, dec_q, ra_t, dec_t)
    
    # Find minimum
    min_idx = np.argmin(dists)
    min_dist = dists[min_idx]
    
    # Check tolerance
    tolerance_deg = tolerance_arcsec * ARCSEC_TO_DEG
    if min_dist <= tolerance_deg:
        return min_idx
    else:
        return None


def calculate_recovery_rate(
    injected_coords: dict,
    recovered_coords: dict,
    tolerance_arcsec: float = 1.0
) -> float:
    """
    Calculate the recovery rate of injected lenses based on coordinate matching.
    
    Args:
        injected_coords: Dictionary mapping injected_id to {'RA': float, 'Dec': float}
        recovered_coords: Dictionary mapping recovered_id to {'RA': float, 'Dec': float}
        tolerance_arcsec: Matching tolerance in arcseconds (default: 1.0)
        
    Returns:
        Recovery rate as a float between 0.0 and 1.0
    """
    if not injected_coords:
        logger.warning("No injected coordinates provided")
        return 0.0
        
    if not recovered_coords:
        logger.warning("No recovered coordinates provided")
        return 0.0
        
    recovered_count = 0
    
    for inj_id, inj_coords in injected_coords.items():
        # Try to find a match in recovered coordinates
        best_match = None
        best_dist = float('inf')
        
        for rec_id, rec_coords in recovered_coords.items():
            dist = angular_distance(
                inj_coords['RA'], inj_coords['Dec'],
                rec_coords['RA'], rec_coords['Dec']
            )
            if dist < best_dist:
                best_dist = dist
                best_match = rec_id
                
        # Check if within tolerance
        tolerance_deg = tolerance_arcsec * ARCSEC_TO_DEG
        if best_dist <= tolerance_deg:
            recovered_count += 1
            
    recovery_rate = recovered_count / len(injected_coords)
    logger.info(f"Recovery rate: {recovery_rate:.4f} ({recovered_count}/{len(injected_coords)})")
    
    return recovery_rate