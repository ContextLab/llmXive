"""
metrics.py - Calculation of topological metrics and derived parameters.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_q_profile(efit_data: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Extract the q-profile from EFIT data.
    
    Args:
        efit_data: Dictionary containing EFIT reconstruction data.
        
    Returns:
        numpy array of q-values or None if not available.
    """
    if not efit_data or 'q_profile' not in efit_data:
        logger.warning("q-profile not found in EFIT data")
        return None
    
    q_profile = efit_data['q_profile']
    if isinstance(q_profile, list):
        return np.array(q_profile)
    return q_profile

def calculate_local_magnetic_shear(q_profile: np.ndarray, rho_tor: np.ndarray) -> Optional[np.ndarray]:
    """
    Calculate local magnetic shear from q-profile.
    s = (r/q) * (dq/dr)
    
    Args:
        q_profile: Array of q-values.
        rho_tor: Array of normalized toroidal radii.
        
    Returns:
        Array of local magnetic shear values or None.
    """
    if q_profile is None or len(q_profile) < 2:
        logger.warning("Insufficient q-profile data for shear calculation")
        return None
    
    # Calculate derivative dq/dr
    dq_dr = np.gradient(q_profile, rho_tor)
    
    # Calculate shear s = (r/q) * (dq/dr)
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        shear = (rho_tor / q_profile) * dq_dr
        shear = np.nan_to_num(shear, nan=0.0, posinf=0.0, neginf=0.0)
    
    return shear

def calculate_resonant_surface_density(q_profile: np.ndarray, rho_tor: np.ndarray) -> float:
    """
    Calculate resonant surface density by counting rational surfaces (q = m/n)
    per unit normalized minor radius.
    
    Uses a loop where m, n ∈ [1, 10] and tolerance |q - m/n| < 0.01.
    
    Args:
        q_profile: Array of q-values at each rho_tor point.
        rho_tor: Array of normalized toroidal radii (0 to 1).
        
    Returns:
        Resonant surface density (count per unit rho_tor).
    """
    if q_profile is None or len(q_profile) < 2:
        logger.warning("Insufficient q-profile data for resonant surface density calculation")
        return 0.0
    
    if rho_tor is None or len(rho_tor) < 2:
        logger.warning("Insufficient rho_tor data for resonant surface density calculation")
        return 0.0
    
    # Define range for m and n
    m_range = range(1, 11)
    n_range = range(1, 11)
    tolerance = 0.01
    
    # Normalize rho_tor to [0, 1] if needed
    rho_min = np.min(rho_tor)
    rho_max = np.max(rho_tor)
    rho_span = rho_max - rho_min
    
    if rho_span < 1e-6:
        logger.warning("rho_tor span is too small")
        return 0.0
    
    # Count rational surfaces
    rational_surface_count = 0
    total_rho_span = rho_span
    
    for m in m_range:
        for n in n_range:
            target_q = m / n
            # Find indices where q is close to target_q
            diff = np.abs(q_profile - target_q)
            matches = diff < tolerance
            
            if np.any(matches):
                rational_surface_count += 1
    
    # Calculate density: count per unit normalized radius
    density = rational_surface_count / total_rho_span if total_rho_span > 0 else 0.0
    
    logger.debug(f"Found {rational_surface_count} rational surfaces in range [1,10]/[1,10]")
    logger.debug(f"Resonant surface density: {density:.4f} per unit rho_tor")
    
    return density

def derive_island_width(
    local_shear: np.ndarray,
    q_profile: np.ndarray,
    Bt_field: float,
    delta_psi: Optional[float] = None
) -> Optional[float]:
    """
    Derive island width using Rutherford equation approximation.
    
    Args:
        local_shear: Local magnetic shear values.
        q_profile: q-profile values.
        Bt_field: Toroidal magnetic field strength (Tesla).
        delta_psi: Perturbation in poloidal flux (optional).
        
    Returns:
        Calculated island width in meters, or None if derivation fails.
    """
    if local_shear is None or q_profile is None:
        logger.warning("Missing shear or q-profile for island width derivation")
        return None
    
    if Bt_field is None or Bt_field <= 0:
        logger.warning("Invalid toroidal field for island width derivation")
        return None
    
    # Use median shear and q for calculation
    s_median = np.median(local_shear)
    q_median = np.median(q_profile)
    
    if s_median == 0:
        logger.warning("Zero shear detected, cannot derive island width")
        return None
    
    # Simplified Rutherford-based estimation
    # w ~ sqrt(delta_psi / (s * Bt))
    # If delta_psi not provided, use a typical perturbation estimate
    if delta_psi is None:
        # Typical perturbation for DIII-D
        delta_psi = 1e-4  # Wb (placeholder, should be from data)
    
    # Calculate island width (simplified model)
    # w = 4 * sqrt(delta_psi / (|s| * q * Bt))
    # This is a heuristic approximation
    try:
        w = 4.0 * np.sqrt(abs(delta_psi) / (abs(s_median) * q_median * Bt_field))
        return float(w)
    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Error deriving island width: {e}")
        return None

def detect_outliers(df: pd.DataFrame, column: str = 'island_width', threshold: float = 0.5) -> List[int]:
    """
    Detect outliers where island_width > minor radius (threshold).
    
    Args:
        df: DataFrame containing the data.
        column: Column name to check.
        threshold: Minor radius threshold (default 0.5m).
        
    Returns:
        List of indices of outlier rows.
    """
    if column not in df.columns:
        logger.warning(f"Column {column} not found in DataFrame")
        return []
    
    outliers = df[df[column] > threshold].index.tolist()
    if outliers:
        logger.warning(f"Found {len(outliers)} outliers where {column} > {threshold}m")
    
    return outliers

def validate_metric_ranges(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that metric values are within expected physical ranges.
    
    Args:
        df: DataFrame with metrics.
        
    Returns:
        Tuple of (is_valid, list of warnings).
    """
    warnings = []
    is_valid = True
    
    if 'resonant_surface_density' in df.columns:
        invalid_rows = df[df['resonant_surface_density'] < 0]
        if not invalid_rows.empty:
            warnings.append(f"Found {len(invalid_rows)} rows with negative resonant_surface_density")
            is_valid = False
    
    if 'island_width' in df.columns:
        invalid_rows = df[df['island_width'] < 0]
        if not invalid_rows.empty:
            warnings.append(f"Found {len(invalid_rows)} rows with negative island_width")
            is_valid = False
    
    return is_valid, warnings

def validate_metric_ranges_for_output(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Additional validation for output metrics before saving.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Tuple of (is_valid, list of warnings).
    """
    return validate_metric_ranges(df)

def process_metrics_for_discharges(
    unified_data: pd.DataFrame,
    efit_data_map: Dict[int, Dict[str, Any]]
) -> pd.DataFrame:
    """
    Process metrics for all discharges in the unified dataset.
    
    Args:
        unified_data: DataFrame with discharge data.
        efit_data_map: Map of discharge_id to EFIT data.
        
    Returns:
        DataFrame with calculated metrics.
    """
    results = []
    
    for idx, row in unified_data.iterrows():
        discharge_id = row['discharge_id']
        efit_data = efit_data_map.get(discharge_id, {})
        
        # Extract q-profile
        q_profile = extract_q_profile(efit_data)
        
        # Assume rho_tor is 0 to 1 linearly spaced if not available
        if q_profile is not None:
            rho_tor = np.linspace(0, 1, len(q_profile))
            
            # Calculate local magnetic shear
            shear = calculate_local_magnetic_shear(q_profile, rho_tor)
            
            # Calculate resonant surface density
            resonant_density = calculate_resonant_surface_density(q_profile, rho_tor)
            
            # Derive island width if needed
            island_width = row.get('island_width')
            if island_width is None or pd.isna(island_width):
                Bt = efit_data.get('Bt_field', 2.0)  # Default DIII-D field
                island_width = derive_island_width(shear, q_profile, Bt)
            
            # Create result row
            result_row = {
                'discharge_id': discharge_id,
                'island_width': island_width,
                'resonant_surface_density': resonant_density,
                'tau_e': row.get('tau_e'),
                'confinement_mode': row.get('confinement_mode'),
                'h98y2': row.get('h98y2')
            }
            results.append(result_row)
        else:
            logger.warning(f"Skipping discharge {discharge_id}: no q-profile available")
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for metrics calculation.
    Reads unified_analysis.csv, calculates metrics, saves to metrics.csv.
    """
    logger.info("Starting metrics calculation")
    
    # Paths
    unified_path = Path("data/processed/unified_analysis.csv")
    output_path = Path("data/processed/metrics.csv")
    
    if not unified_path.exists():
        logger.error(f"Unified analysis file not found: {unified_path}")
        return
    
    # Load unified data
    df = pd.read_csv(unified_path)
    logger.info(f"Loaded {len(df)} discharges from {unified_path}")
    
    # Simulate EFIT data map (in real scenario, this would come from retrieval)
    # For now, we process what we have
    efit_data_map = {}
    for discharge_id in df['discharge_id'].unique():
        # Placeholder: in real implementation, fetch EFIT data here
        efit_data_map[discharge_id] = {}
    
    # Process metrics
    metrics_df = process_metrics_for_discharges(df, efit_data_map)
    
    # Validate
    is_valid, warnings = validate_metric_ranges_for_output(metrics_df)
    for w in warnings:
        logger.warning(w)
    
    # Save
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")
    
    return metrics_df

if __name__ == "__main__":
    main()
