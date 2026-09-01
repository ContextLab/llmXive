import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_resonant_surface_density(
    q_profile: np.ndarray,
    rho_tor_profile: np.ndarray,
    m_min: int = 2,
    m_max: int = 12,
    n_min: int = 1,
    n_max: int = 6,
    tolerance: float = 0.01
) -> float:
    """
    Calculate resonant surface density by counting rational surfaces (q = m/n)
    per unit normalized minor radius (rho_tor).

    A surface is considered rational if |q - m/n| < tolerance.
    The density is the count of unique rational surfaces divided by the
    range of rho_tor (rho_tor_max - rho_tor_min).

    Args:
        q_profile: Array of q values corresponding to rho_tor_profile.
        rho_tor_profile: Array of normalized toroidal radius values.
        m_min: Lower bound for toroidal mode number m (inclusive).
        m_max: Upper bound for toroidal mode number m (inclusive).
        n_min: Lower bound for poloidal mode number n (inclusive).
        n_max: Upper bound for poloidal mode number n (inclusive).
        tolerance: Tolerance for rational surface identification.

    Returns:
        Resonant surface density (count per unit rho_tor). Returns 0 if
        q_profile is empty or no rational surfaces are found.
    """
    if q_profile is None or len(q_profile) == 0:
        logger.warning("q_profile is empty or None. Returning density 0.")
        return 0.0

    if rho_tor_profile is None or len(rho_tor_profile) == 0:
        logger.warning("rho_tor_profile is empty or None. Returning density 0.")
        return 0.0

    if len(q_profile) != len(rho_tor_profile):
        raise ValueError("q_profile and rho_tor_profile must have the same length.")

    valid_mask = ~np.isnan(q_profile) & ~np.isnan(rho_tor_profile)
    q_valid = q_profile[valid_mask]
    rho_valid = rho_tor_profile[valid_mask]

    if len(q_valid) == 0:
        logger.warning("No valid data points in q_profile after masking NaNs. Returning density 0.")
        return 0.0

    rho_range = np.max(rho_valid) - np.min(rho_valid)
    if rho_range <= 0:
        logger.warning("rho_tor range is zero or negative. Returning density 0.")
        return 0.0

    rational_surfaces = set()

    for m in range(m_min, m_max + 1):
        for n in range(n_min, n_max + 1):
            q_rational = m / n
            # Check if any q value in the profile is close to m/n
            if np.any(np.abs(q_valid - q_rational) < tolerance):
                rational_surfaces.add(q_rational)

    density = len(rational_surfaces) / rho_range
    logger.debug(f"Found {len(rational_surfaces)} rational surfaces in q-range [{np.min(q_valid):.3f}, {np.max(q_valid):.3f}]. Density: {density:.4f}")
    return density

def detect_outliers(df: pd.DataFrame, island_width_col: str = 'island_width', minor_radius_col: str = 'minor_radius') -> List[int]:
    """
    Flag and exclude discharges where island_width > minor_radius.

    Args:
        df: DataFrame containing discharge data.
        island_width_col: Column name for island width.
        minor_radius_col: Column name for minor radius.

    Returns:
        List of indices (rows) that are outliers.
    """
    if island_width_col not in df.columns or minor_radius_col not in df.columns:
        logger.warning(f"Columns {island_width_col} or {minor_radius_col} not found. No outliers detected.")
        return []

    outliers = df[df[island_width_col] > df[minor_radius_col]].index.tolist()
    if outliers:
        logger.warning(f"Detected {len(outliers)} outliers where island_width > minor_radius.")
    return outliers

def validate_metric_ranges(df: pd.DataFrame, metrics: Dict[str, Tuple[float, float]]) -> bool:
    """
    Validate that metric values fall within specified ranges.

    Args:
        df: DataFrame containing metric values.
        metrics: Dictionary mapping metric name to (min, max) tuple.

    Returns:
        True if all metrics are within range, False otherwise.
    """
    valid = True
    for metric_name, (min_val, max_val) in metrics.items():
        if metric_name not in df.columns:
            logger.warning(f"Metric {metric_name} not found in DataFrame.")
            valid = False
            continue

        if (df[metric_name] < min_val).any() or (df[metric_name] > max_val).any():
            logger.warning(f"Metric {metric_name} has values outside range [{min_val}, {max_val}].")
            valid = False
    return valid

def process_metrics_for_discharges(
    data_dir: Path,
    output_path: Path,
    m_min: int = 2,
    m_max: int = 12,
    n_min: int = 1,
    n_max: int = 6,
    tolerance: float = 0.01
) -> pd.DataFrame:
    """
    Process multiple discharges to calculate resonant surface density.
    Reads from a unified analysis CSV (produced by US1), extracts q-profiles,
    calculates density, and outputs a metrics CSV.

    Args:
        data_dir: Directory containing the unified analysis CSV.
        output_path: Path to write the metrics CSV.
        m_min, m_max, n_min, n_max, tolerance: Parameters for density calculation.

    Returns:
        DataFrame containing the calculated metrics.
    """
    input_file = data_dir / "unified_analysis.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Reading unified data from {input_file}")
    df = pd.read_csv(input_file)

    required_cols = ['discharge_id', 'q_profile', 'rho_tor_profile']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")

    # q_profile and rho_tor_profile are stored as string representations of lists
    # We need to parse them into numpy arrays
    def parse_array(s: str) -> np.ndarray:
        s = s.strip('[]')
        if not s:
            return np.array([])
        return np.array([float(x.strip()) for x in s.split(',')])

    results = []

    for _, row in df.iterrows():
        discharge_id = row['discharge_id']
        q_arr = parse_array(row['q_profile'])
        rho_arr = parse_array(row['rho_tor_profile'])

        density = calculate_resonant_surface_density(
            q_arr, rho_arr,
            m_min=m_min, m_max=m_max,
            n_min=n_min, n_max=n_max,
            tolerance=tolerance
        )

        results.append({
            'discharge_id': discharge_id,
            'resonant_surface_density': density,
            'q_profile_length': len(q_arr),
            'rho_tor_range': np.max(rho_arr) - np.min(rho_arr) if len(rho_arr) > 0 else 0.0
        })

    metrics_df = pd.DataFrame(results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Metrics saved to {output_path}")
    return metrics_df
