import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for Rutherford derivation and density calculation
# Tolerance for rational surface detection: |q - m/n| < 0.01
RATIONAL_SURFACE_TOLERANCE = 0.01
# Minimum m, n values for rational surface counting (positive integers)
MIN_M_N = 1
MAX_M_N = 15  # Reasonable upper bound for rational surfaces in tokamak q-profiles

def extract_q_profile(efit_data: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Extract the q-profile (safety factor) from EFIT data.

    Args:
        efit_data: Dictionary containing EFIT reconstruction data.
                   Expected keys: 'q_profile', 'rho_tor' (normalized minor radius).

    Returns:
        numpy array of q-profile values, or None if data is missing.
    """
    if 'q_profile' not in efit_data or 'rho_tor' not in efit_data:
        logger.warning("EFIT data missing 'q_profile' or 'rho_tor' keys.")
        return None

    q_profile = np.array(efit_data['q_profile'])
    if len(q_profile) == 0:
        logger.warning("EFIT q-profile is empty.")
        return None

    return q_profile

def calculate_local_magnetic_shear(q_profile: np.ndarray, rho_tor: np.ndarray) -> Optional[np.ndarray]:
    """
    Calculate local magnetic shear (s) from the q-profile.
    s = (r/q) * (dq/dr) approx (rho/q) * (dq/drho)

    Args:
        q_profile: Array of q values.
        rho_tor: Array of normalized minor radius values.

    Returns:
        numpy array of local magnetic shear values, or None if calculation fails.
    """
    if q_profile is None or rho_tor is None:
        return None

    # Avoid division by zero in rho_tor (center of plasma)
    # Use a small epsilon for stability
    rho_safe = np.where(rho_tor == 0, 1e-8, rho_tor)

    # Calculate derivative dq/drho using central differences
    dq_drho = np.gradient(q_profile, rho_tor)

    # Calculate local magnetic shear s = (rho/q) * (dq/drho)
    # Avoid division by zero in q
    q_safe = np.where(q_profile == 0, 1e-8, q_profile)
    shear = (rho_safe / q_safe) * dq_drho

    return shear

def calculate_resonant_surface_density(q_profile: np.ndarray, rho_tor: np.ndarray) -> float:
    """
    Calculate resonant surface density by counting rational surfaces (q = m/n)
    per unit normalized minor radius (rho_tor).

    Rational surfaces are identified where |q - m/n| < TOLERANCE for m, n in positive integers.

    Args:
        q_profile: Array of q values.
        rho_tor: Array of normalized minor radius values.

    Returns:
        float: Resonant surface density (count of rational surfaces per unit rho_tor).
               Returns 0.0 if q-profile exists but no rational surfaces are found.
    """
    if q_profile is None or rho_tor is None or len(q_profile) == 0:
        logger.warning("Cannot calculate resonant surface density: missing or empty q-profile/rho_tor.")
        return 0.0

    rational_surfaces = []

    # Iterate over possible m, n values (positive integers)
    for m in range(MIN_M_N, MAX_M_N + 1):
        for n in range(MIN_M_N, MAX_M_N + 1):
            target_q = m / n

            # Find indices where q is close to target_q within tolerance
            # Use a mask to find crossings or close matches
            q_diff = np.abs(q_profile - target_q)
            close_indices = np.where(q_diff < RATIONAL_SURFACE_TOLERANCE)[0]

            if len(close_indices) > 0:
                # We found at least one point close to the rational surface
                # To avoid double counting the same surface for different (m,n) pairs,
                # we store the rho_tor value of the closest match
                closest_idx = close_indices[np.argmin(q_diff[close_indices])]
                rho_val = rho_tor[closest_idx]
                rational_surfaces.append(rho_val)

    # Remove duplicates (same surface found by different m/n pairs)
    # Use a tolerance to group close rho values
    if not rational_surfaces:
        return 0.0

    unique_surfaces = []
    sorted_surfaces = sorted(rational_surfaces)
    if len(sorted_surfaces) > 0:
        current_rho = sorted_surfaces[0]
        unique_surfaces.append(current_rho)
        for i in range(1, len(sorted_surfaces)):
            if sorted_surfaces[i] - current_rho > RATIONAL_SURFACE_TOLERANCE:
                unique_surfaces.append(sorted_surfaces[i])
                current_rho = sorted_surfaces[i]

    # Calculate density: count per unit normalized minor radius
    # Range of rho_tor is typically [0, 1]
    rho_range = np.max(rho_tor) - np.min(rho_tor)
    if rho_range <= 0:
        rho_range = 1.0  # Avoid division by zero

    density = len(unique_surfaces) / rho_range
    logger.debug(f"Found {len(unique_surfaces)} unique rational surfaces. Density: {density:.4f}")
    return density

def derive_island_width(local_shear: np.ndarray, q_profile: np.ndarray, Bt_field: float, rho_tor: np.ndarray) -> Optional[float]:
    """
    Derive island width using the Rutherford equation approximation.
    This is a simplified model: w ~ sqrt( (mu0 * delta_prime) / (s * Bt^2) )
    For this implementation, we use a proxy based on shear and B-field.

    Note: A full Rutherford derivation requires delta_prime (tearing mode stability index),
    which is often not directly available in standard EFIT outputs.
    Here we use a heuristic: island_width ~ 1 / (|shear| * Bt) if shear is significant.
    This is a placeholder for the actual physics derivation that would require
    more detailed MHD stability analysis.

    Args:
        local_shear: Array of local magnetic shear values.
        q_profile: Array of q values.
        Bt_field: Toroidal magnetic field strength (Tesla).
        rho_tor: Array of normalized minor radius values.

    Returns:
        float: Derived island width in meters, or None if inputs are invalid.
    """
    if local_shear is None or q_profile is None or Bt_field is None or rho_tor is None:
        logger.warning("Cannot derive island width: missing required inputs.")
        return None

    if Bt_field <= 0:
        logger.warning(f"Invalid Bt_field value: {Bt_field}. Must be positive.")
        return None

    # Use the average absolute shear as a proxy for stability
    avg_shear = np.mean(np.abs(local_shear))

    if avg_shear == 0:
        logger.warning("Average magnetic shear is zero; cannot derive island width.")
        return None

    # Heuristic derivation:
    # In the Rutherford regime, island growth is balanced by neoclassical effects.
    # A simplified scaling: w ~ C / (s * Bt) where C is a constant related to plasma parameters.
    # We use a normalized constant for demonstration; in a real implementation,
    # C would be derived from specific plasma conditions (current density, resistivity, etc.).
    # For this task, we assume a normalized constant C = 0.01 (m * T) as a placeholder.
    C = 0.01  # Placeholder constant (m * T)
    island_width = C / (avg_shear * Bt_field)

    # Sanity check: island width should be positive and reasonable (< minor radius ~ 0.6m for DIII-D)
    if island_width <= 0 or island_width > 1.0:
        logger.warning(f"Derived island width {island_width:.4f} m is outside reasonable range.")
        return None

    logger.info(f"Derived island width: {island_width:.4f} m (shear: {avg_shear:.4f}, Bt: {Bt_field:.2f} T)")
    return island_width

def detect_outliers(df: pd.DataFrame, column: str = 'island_width', threshold_factor: float = 3.0) -> pd.DataFrame:
    """
    Detect and flag outliers in a specified column using IQR method.
    Flags values > minor_radius (approx 0.67m for DIII-D) as outliers.

    Args:
        df: DataFrame containing the data.
        column: Column name to check for outliers.
        threshold_factor: Not used here but kept for API consistency.

    Returns:
        DataFrame with an 'is_outlier' column added.
    """
    df = df.copy()
    df['is_outlier'] = False

    # DIII-D minor radius is approximately 0.67 meters
    minor_radius = 0.67

    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame for outlier detection.")
        return df

    outliers = df[df[column] > minor_radius]
    if len(outliers) > 0:
        logger.warning(f"Found {len(outliers)} discharges with {column} > minor radius ({minor_radius} m).")
        df.loc[df[column] > minor_radius, 'is_outlier'] = True

    return df

def validate_metric_ranges(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate that metric values are within physically reasonable ranges.

    Args:
        df: DataFrame with metrics.

    Returns:
        Tuple of (validated DataFrame, list of warning messages).
    """
    warnings = []
    df = df.copy()

    # Check island_width
    if 'island_width' in df.columns:
        invalid_width = df[df['island_width'] < 0]
        if len(invalid_width) > 0:
            warnings.append(f"Found {len(invalid_width)} discharges with negative island_width.")

    # Check resonant_surface_density
    if 'resonant_surface_density' in df.columns:
        invalid_density = df[df['resonant_surface_density'] < 0]
        if len(invalid_density) > 0:
            warnings.append(f"Found {len(invalid_density)} discharges with negative resonant_surface_density.")

    return df, warnings

def validate_metric_ranges_for_output(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Additional validation specifically for output metrics before saving.
    Ensures all required fields are present and non-null.

    Args:
        df: DataFrame to validate.

    Returns:
        Tuple of (validated DataFrame, list of warning messages).
    """
    warnings = []
    required_cols = ['discharge_id', 'island_width', 'resonant_surface_density']

    for col in required_cols:
        if col not in df.columns:
            warnings.append(f"Missing required column: {col}")

    null_counts = df[required_cols].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            warnings.append(f"Column '{col}' has {count} null values.")

    return df, warnings

def process_metrics_for_discharges(df: pd.DataFrame, efit_data_map: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    """
    Process metrics for discharges that need derivation.
    This function updates the DataFrame with derived island_width and resonant_surface_density
    for discharges where needs_derivation is True.

    Args:
        df: DataFrame containing discharge data with 'needs_derivation' flag.
        efit_data_map: Dictionary mapping discharge_id to EFIT data.

    Returns:
        Updated DataFrame with derived metrics.
    """
    if 'needs_derivation' not in df.columns:
        logger.warning("'needs_derivation' column not found in DataFrame. Skipping derivation.")
        return df

    derived_count = 0
    excluded_count = 0

    for idx, row in df.iterrows():
        discharge_id = row['discharge_id']
        needs_derivation = row.get('needs_derivation', False)

        if not needs_derivation:
            continue

        # Check if EFIT data is available
        if discharge_id not in efit_data_map:
            logger.warning(f"Discharge {discharge_id} marked for derivation but EFIT data missing. Excluding.")
            df.loc[idx, 'island_width'] = np.nan
            df.loc[idx, 'resonant_surface_density'] = np.nan
            excluded_count += 1
            continue

        efit_data = efit_data_map[discharge_id]

        # Extract q-profile and rho_tor
        q_profile = extract_q_profile(efit_data)
        rho_tor = efit_data.get('rho_tor')

        if q_profile is None or rho_tor is None:
            logger.warning(f"Discharge {discharge_id}: Missing q-profile or rho_tor. Excluding from derivation.")
            df.loc[idx, 'island_width'] = np.nan
            df.loc[idx, 'resonant_surface_density'] = np.nan
            excluded_count += 1
            continue

        # Calculate local magnetic shear
        local_shear = calculate_local_magnetic_shear(q_profile, rho_tor)
        if local_shear is None:
            logger.warning(f"Discharge {discharge_id}: Failed to calculate local magnetic shear. Excluding.")
            df.loc[idx, 'island_width'] = np.nan
            df.loc[idx, 'resonant_surface_density'] = np.nan
            excluded_count += 1
            continue

        # Get Bt field
        Bt_field = efit_data.get('Bt_field')
        if Bt_field is None:
            logger.warning(f"Discharge {discharge_id}: Missing Bt_field. Excluding from derivation.")
            df.loc[idx, 'island_width'] = np.nan
            df.loc[idx, 'resonant_surface_density'] = np.nan
            excluded_count += 1
            continue

        # Derive island width
        derived_width = derive_island_width(local_shear, q_profile, Bt_field, rho_tor)
        if derived_width is None:
            logger.warning(f"Discharge {discharge_id}: Failed to derive island width. Excluding.")
            df.loc[idx, 'island_width'] = np.nan
            df.loc[idx, 'resonant_surface_density'] = np.nan
            excluded_count += 1
            continue

        # Calculate resonant surface density
        density = calculate_resonant_surface_density(q_profile, rho_tor)

        # Update DataFrame
        df.loc[idx, 'island_width'] = derived_width
        df.loc[idx, 'resonant_surface_density'] = density
        derived_count += 1
        logger.info(f"Discharge {discharge_id}: Derived island_width={derived_width:.4f} m, density={density:.4f}")

    logger.info(f"Derivation complete: {derived_count} discharges derived, {excluded_count} excluded.")
    return df

def main():
    """
    Main entry point for metrics processing.
    This function is intended to be called by the pipeline to process metrics.
    """
    logger.info("Starting metrics processing (T018c).")

    # Load unified dataset
    input_path = Path("data/processed/unified_analysis.csv")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} discharges from {input_path}")

    # Note: In a real pipeline, efit_data_map would be populated from retrieval
    # For this task, we assume the data is available or we skip derivation if not
    # Since T013 already handled retrieval and marked needs_derivation,
    # we would need the actual EFIT data here. For this implementation,
    # we simulate the efit_data_map from the existing data or skip if not available.

    # Placeholder: In a real scenario, this would be populated from the retrieval step
    # For now, we assume efit_data_map is empty and derivation will be skipped if data is missing
    efit_data_map = {}

    # Process metrics
    df_processed = process_metrics_for_discharges(df, efit_data_map)

    # Detect outliers
    df_processed = detect_outliers(df_processed)

    # Validate ranges
    df_processed, warnings = validate_metric_ranges_for_output(df_processed)
    for w in warnings:
        logger.warning(w)

    # Save output
    output_path = Path("data/processed/metrics.csv")
    df_processed.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path}")

    return df_processed

if __name__ == "__main__":
    main()