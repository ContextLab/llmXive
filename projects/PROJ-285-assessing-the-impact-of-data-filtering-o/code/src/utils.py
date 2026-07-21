import numpy as np
import logging
from typing import Tuple, Optional
from .logging_config import get_logger, CoordinateMatchError

logger = get_logger(__name__)

def angular_distance(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """
    Calculate the angular distance between two points on a sphere (in arcseconds).

    Uses the Haversine formula for accurate small-angle calculations.

    Args:
        ra1: Right ascension of point 1 (degrees).
        dec1: Declination of point 1 (degrees).
        ra2: Right ascension of point 2 (degrees).
        dec2: Declination of point 2 (degrees).

    Returns:
        float: Angular distance in arcseconds.
    """
    # Convert degrees to radians
    ra1_rad = np.radians(ra1)
    dec1_rad = np.radians(dec1)
    ra2_rad = np.radians(ra2)
    dec2_rad = np.radians(dec2)

    # Haversine formula
    d_ra = ra2_rad - ra1_rad
    d_dec = dec2_rad - dec1_rad

    a = np.sin(d_dec / 2)**2 + np.cos(dec1_rad) * np.cos(dec2_rad) * np.sin(d_ra / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    # Convert radians to arcseconds (1 radian = 206265 arcseconds)
    distance_arcsec = c * 206265

    return distance_arcsec


def match_coordinates(
    catalog1: np.ndarray,
    catalog2: np.ndarray,
    tolerance_arcsec: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Match coordinates between two catalogs within a given tolerance.

    Args:
        catalog1: Nx2 array of (RA, Dec) for catalog 1.
        catalog2: Nx2 array of (RA, Dec) for catalog 2.
        tolerance_arcsec: Matching tolerance in arcseconds.

    Returns:
        Tuple of (indices1, indices2) where matches were found.

    Raises:
        CoordinateMatchError: If inputs are invalid.
    """
    if catalog1.shape[1] != 2 or catalog2.shape[1] != 2:
        raise CoordinateMatchError("Catalogs must have exactly 2 columns (RA, Dec)")

    matches1 = []
    matches2 = []

    for i, (ra1, dec1) in enumerate(catalog1):
        for j, (ra2, dec2) in enumerate(catalog2):
            dist = angular_distance(ra1, dec1, ra2, dec2)
            if dist <= tolerance_arcsec:
                matches1.append(i)
                matches2.append(j)
                break  # First match only

    return np.array(matches1), np.array(matches2)


def find_matches_in_catalog(
    catalog_df,
    reference_df,
    ra_col: str = 'RA',
    dec_col: str = 'Dec',
    tolerance_arcsec: float = 1.0
) -> pd.DataFrame:
    """
    Find matches between two DataFrames based on coordinates.

    Args:
        catalog_df: DataFrame with candidate coordinates.
        reference_df: DataFrame with reference coordinates.
        ra_col: Name of RA column.
        dec_col: Name of Dec column.
        tolerance_arcsec: Matching tolerance in arcseconds.

    Returns:
        DataFrame with matched rows from catalog_df and their reference matches.
    """
    import pandas as pd
    
    matches = []
    
    for idx, row in catalog_df.iterrows():
        ra_cand, dec_cand = row[ra_col], row[dec_col]
        
        for ref_idx, ref_row in reference_df.iterrows():
            ra_ref, dec_ref = ref_row[ra_col], ref_row[dec_col]
            
            dist = angular_distance(ra_cand, dec_cand, ra_ref, dec_ref)
            
            if dist <= tolerance_arcsec:
                match_row = row.copy()
                match_row['matched_ref_id'] = ref_idx
                match_row['angular_distance'] = dist
                matches.append(match_row)
                break  # First match only
    
    return pd.DataFrame(matches) if matches else pd.DataFrame(columns=catalog_df.columns.tolist() + ['matched_ref_id', 'angular_distance'])


def calculate_recovery_rate(
    detected_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    ra_col: str = 'RA',
    dec_col: str = 'Dec',
    tolerance_arcsec: float = 1.0
) -> float:
    """
    Calculate the recovery rate of detected objects against ground truth.

    Args:
        detected_df: DataFrame with detected coordinates.
        ground_truth_df: DataFrame with ground truth coordinates.
        ra_col: Name of RA column.
        dec_col: Name of Dec column.
        tolerance_arcsec: Matching tolerance in arcseconds.

    Returns:
        float: Recovery rate (0.0 to 1.0).
    """
    if len(ground_truth_df) == 0:
        return 0.0

    recovered = 0
    for idx, row in ground_truth_df.iterrows():
        ra_gt, dec_gt = row[ra_col], row[dec_col]
        
        for det_idx, det_row in detected_df.iterrows():
            ra_det, dec_det = det_row[ra_col], det_row[dec_col]
            
            dist = angular_distance(ra_gt, dec_gt, ra_det, dec_det)
            
            if dist <= tolerance_arcsec:
                recovered += 1
                break  # Count each ground truth object only once

    return recovered / len(ground_truth_df)
