import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for rational surface search
MIN_RATIONAL_DENOMINATOR = 1
MAX_RATIONAL_DENOMINATOR = 20
MIN_RATIONAL_NUMERATOR = 1
MAX_RATIONAL_NUMERATOR = 20
TOLERANCE = 0.01

def calculate_resonant_surface_density(
    q_profile: np.ndarray,
    rho_tor_profile: np.ndarray,
    m_min: int = MIN_RATIONAL_NUMERATOR,
    m_max: int = MAX_RATIONAL_NUMERATOR,
    n_min: int = MIN_RATIONAL_DENOMINATOR,
    n_max: int = MAX_RATIONAL_DENOMINATOR,
    tolerance: float = TOLERANCE
) -> float:
    """
    Calculate resonant surface density by counting rational surfaces (q = m/n)
    per unit normalized minor radius (rho_tor).

    A surface is considered rational if |q - m/n| < tolerance.
    The density is calculated as the count of unique rational surfaces found
    divided by the range of rho_tor covered by the profile.

    Args:
        q_profile: Array of q values at each rho_tor point.
        rho_tor_profile: Array of normalized minor radius values (0 to 1).
        m_min: Lower bound for toroidal mode number m (inclusive).
        m_max: Upper bound for toroidal mode number m (inclusive).
        n_min: Lower bound for poloidal mode number n (inclusive).
        n_max: Upper bound for poloidal mode number n (inclusive).
        tolerance: Tolerance for matching q to m/n.

    Returns:
        Resonant surface density (count of rational surfaces per unit rho_tor).
        Returns 0.0 if no rational surfaces are found or if rho_tor range is 0.
    """
    if len(q_profile) == 0 or len(rho_tor_profile) == 0:
        logger.warning("Empty q_profile or rho_tor_profile provided.")
        return 0.0

    if len(q_profile) != len(rho_tor_profile):
        raise ValueError("q_profile and rho_tor_profile must have the same length.")

    # Filter out NaN values
    valid_mask = ~np.isnan(q_profile) & ~np.isnan(rho_tor_profile)
    q_clean = q_profile[valid_mask]
    rho_clean = rho_tor_profile[valid_mask]

    if len(q_clean) == 0:
        logger.warning("No valid data points after filtering NaNs.")
        return 0.0

    # Calculate rho_tor range
    rho_min = np.min(rho_clean)
    rho_max = np.max(rho_clean)
    rho_range = rho_max - rho_min

    if rho_range <= 0:
        logger.warning("rho_tor range is zero or negative. Cannot calculate density.")
        return 0.0

    # Generate all possible rational numbers m/n within bounds
    rational_values = set()
    for m in range(m_min, m_max + 1):
        for n in range(n_min, n_max + 1):
            if n == 0:
                continue
            rational_values.add(m / n)

    rational_list = sorted(list(rational_values))

    # Count unique rational surfaces found in the profile
    found_surfaces = set()

    # For each q value in the profile, check if it matches any rational m/n
    for q_val in q_clean:
        if np.isnan(q_val):
            continue
        for rational in rational_list:
            if abs(q_val - rational) < tolerance:
                found_surfaces.add(rational)
                break  # Count each q point only once, even if it matches multiple rationals

    count = len(found_surfaces)
    density = count / rho_range

    logger.debug(f"Found {count} unique rational surfaces in rho_tor range [{rho_min:.3f}, {rho_max:.3f}]. Density: {density:.4f}")
    return density

def detect_outliers(
    df: pd.DataFrame,
    island_width_col: str = 'island_width',
    minor_radius_col: str = 'minor_radius'
) -> pd.DataFrame:
    """
    Flag and exclude discharges where island_width > minor radius.

    Args:
        df: DataFrame containing discharge data.
        island_width_col: Column name for island width.
        minor_radius_col: Column name for minor radius.

    Returns:
        DataFrame with a new column 'is_outlier' (True if island_width > minor_radius).
        Rows where is_outlier is True should be excluded from further analysis.
    """
    if island_width_col not in df.columns or minor_radius_col not in df.columns:
        missing = [c for c in [island_width_col, minor_radius_col] if c not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")

    # Create outlier flag
    df['is_outlier'] = df[island_width_col] > df[minor_radius_col]
    outlier_count = df['is_outlier'].sum()
    logger.info(f"Detected {outlier_count} outliers where island_width > minor_radius.")

    return df

def validate_metric_ranges(
    df: pd.DataFrame,
    metrics_cols: List[str] = ['resonant_surface_density', 'island_width', 'minor_radius']
) -> Tuple[bool, List[str]]:
    """
    Validate that metric values are within physically reasonable ranges.

    Args:
        df: DataFrame containing metric data.
        metrics_cols: List of column names to validate.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    for col in metrics_cols:
        if col not in df.columns:
            errors.append(f"Column '{col}' not found in DataFrame.")
            continue

        if df[col].isna().any():
            errors.append(f"Column '{col}' contains NaN values.")

        if np.any(df[col] < 0):
            errors.append(f"Column '{col}' contains negative values.")

    is_valid = len(errors) == 0
    return is_valid, errors

def process_metrics_for_discharges(
    df: pd.DataFrame,
    q_profile_col: str = 'q_profile',
    rho_tor_col: str = 'rho_tor_profile',
    m_min: int = MIN_RATIONAL_NUMERATOR,
    m_max: int = MAX_RATIONAL_NUMERATOR,
    n_min: int = MIN_RATIONAL_DENOMINATOR,
    n_max: int = MAX_RATIONAL_DENOMINATOR,
    tolerance: float = TOLERANCE
) -> pd.DataFrame:
    """
    Process a DataFrame of discharges to calculate resonant_surface_density for each.

    Args:
        df: DataFrame with discharge data, including q_profile and rho_tor_profile columns.
        q_profile_col: Column name containing q-profile arrays.
        rho_tor_col: Column name containing rho_tor-profile arrays.
        m_min, m_max: Range for toroidal mode number m.
        n_min, n_max: Range for poloidal mode number n.
        tolerance: Tolerance for rational surface matching.

    Returns:
        DataFrame with a new column 'resonant_surface_density'.
    """
    if q_profile_col not in df.columns or rho_tor_col not in df.columns:
        raise ValueError(f"Missing required columns: {q_profile_col}, {rho_tor_col}")

    densities = []
    for idx, row in df.iterrows():
        q_prof = row[q_profile_col]
        rho_prof = row[rho_tor_col]

        # Convert to numpy arrays if they are lists
        if isinstance(q_prof, list):
            q_prof = np.array(q_prof)
        if isinstance(rho_prof, list):
            rho_prof = np.array(rho_prof)

        density = calculate_resonant_surface_density(
            q_prof, rho_prof, m_min, m_max, n_min, n_max, tolerance
        )
        densities.append(density)

    df['resonant_surface_density'] = densities
    logger.info(f"Calculated resonant_surface_density for {len(df)} discharges.")

    return df
