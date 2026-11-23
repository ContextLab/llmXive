"""
Preprocessing module for DIII-D discharge data.
Handles alignment, extraction, parsing, and saving of unified datasets.
"""

import logging
import numpy as np
import pandas as pd
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
REQUIRED_COLUMNS = [
    'discharge_id',
    'island_width',
    'resonant_surface_density',
    'tau_e',
    'confinement_mode',
    'h98y2',
    'q_min',
    'q_max',
    'te_profile',
    'ne_profile'
]

OUTPUT_PATH = Path("data/processed/unified_analysis.csv")
CHECKSUM_PATH = Path("data/processed/unified_analysis.csv.sha256")


def align_time_series(
    time_series_list: List[Tuple[np.ndarray, np.ndarray]],
    target_time: float,
    tolerance: float = 0.01
) -> Optional[np.ndarray]:
    """
    Align multiple time series to a specific target time.
    
    Args:
        time_series_list: List of (time_array, value_array) tuples
        target_time: Target time for alignment
        tolerance: Time tolerance for matching points
        
    Returns:
        Interpolated values at target_time, or None if alignment fails
    """
    if not time_series_list:
        return None
        
    # Simple interpolation approach
    all_times = np.concatenate([t for t, _ in time_series_list])
    all_values = np.concatenate([v for _, v in time_series_list])
    
    if len(all_times) < 2:
        return None
        
    try:
        # Sort by time
        sorted_indices = np.argsort(all_times)
        sorted_times = all_times[sorted_indices]
        sorted_values = all_values[sorted_indices]
        
        # Interpolate
        interpolated = np.interp(target_time, sorted_times, sorted_values)
        return interpolated
    except Exception as e:
        logger.warning(f"Time series alignment failed: {e}")
        return None


def extract_snapshot(
    data_dict: Dict[str, Any],
    target_time: float,
    tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Extract a snapshot of data at a specific time.
    
    Args:
        data_dict: Dictionary containing time-series data
        target_time: Target time for extraction
        tolerance: Time tolerance
        
    Returns:
        Dictionary with values at target_time
    """
    snapshot = {}
    for key, value in data_dict.items():
        if isinstance(value, tuple) and len(value) == 2:
            time_arr, val_arr = value
            if len(time_arr) > 0 and len(val_arr) > 0:
                try:
                    sorted_indices = np.argsort(time_arr)
                    sorted_times = time_arr[sorted_indices]
                    sorted_vals = val_arr[sorted_indices]
                    snapshot[key] = np.interp(target_time, sorted_times, sorted_vals)
                except Exception as e:
                    logger.warning(f"Snapshot extraction failed for {key}: {e}")
                    snapshot[key] = None
        else:
            snapshot[key] = value
            
    return snapshot


def calculate_island_width(
    q_profile: np.ndarray,
    rational_surfaces: List[Tuple[int, int]],
    minor_radius: float
) -> float:
    """
    Calculate island width based on q-profile and rational surfaces.
    
    Args:
        q_profile: Q-profile values
        rational_surfaces: List of (m, n) tuples for rational surfaces
        minor_radius: Minor radius of the device
        
    Returns:
        Calculated island width in meters
    """
    if q_profile is None or len(q_profile) == 0:
        return 0.0
        
    island_width = 0.0
    for m, n in rational_surfaces:
        target_q = m / n
        # Find where q crosses target_q
        crossings = np.where(np.diff(np.sign(q_profile - target_q)))[0]
        if len(crossings) > 0:
            # Simplified width calculation
            width = minor_radius * 0.01  # Placeholder calculation
            island_width = max(island_width, width)
            
    return island_width


def determine_confinement_mode(h98y2: float) -> str:
    """
    Determine confinement mode based on H-factor.
    
    Args:
        h98y2: H98(y,2) confinement enhancement factor
        
    Returns:
        'H-mode' if h98y2 >= 0.85, else 'L-mode'
    """
    if h98y2 is None:
        return 'L-mode'
    return 'H-mode' if h98y2 >= 0.85 else 'L-mode'


def parse_discharge_data(
    discharge_data: Dict[str, Any],
    discharge_id: int
) -> Optional[Dict[str, Any]]:
    """
    Parse raw discharge data into a structured dictionary.
    
    Args:
        discharge_data: Raw data from MDSplus
        discharge_id: Discharge identifier
        
    Returns:
        Structured data dictionary or None if parsing fails
    """
    try:
        # Extract key metrics
        island_width = discharge_data.get('island_width', 0.0)
        if island_width is None:
            island_width = 0.0
            
        resonant_density = discharge_data.get('resonant_surface_density', 0.0)
        if resonant_density is None:
            resonant_density = 0.0
            
        tau_e = discharge_data.get('tau_e', 0.0)
        if tau_e is None:
            tau_e = 0.0
            
        h98y2 = discharge_data.get('h98y2', 0.0)
        if h98y2 is None:
            h98y2 = 0.0
            
        confinement_mode = determine_confinement_mode(h98y2)
        
        q_min = discharge_data.get('q_min', 0.0)
        q_max = discharge_data.get('q_max', 0.0)
        
        # Extract profiles
        te_profile = discharge_data.get('te_profile', [])
        ne_profile = discharge_data.get('ne_profile', [])
        
        # Convert profiles to lists if they are arrays
        if isinstance(te_profile, np.ndarray):
            te_profile = te_profile.tolist()
        if isinstance(ne_profile, np.ndarray):
            ne_profile = ne_profile.tolist()
            
        parsed_data = {
            'discharge_id': int(discharge_id),
            'island_width': float(island_width),
            'resonant_surface_density': float(resonant_density),
            'tau_e': float(tau_e),
            'confinement_mode': confinement_mode,
            'h98y2': float(h98y2),
            'q_min': float(q_min),
            'q_max': float(q_max),
            'te_profile': te_profile,
            'ne_profile': ne_profile
        }
        
        logger.info(f"Parsed data for discharge {discharge_id}")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Failed to parse data for discharge {discharge_id}: {e}")
        return None


def process_multiple_discharges(
    discharge_list: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Process multiple discharges into a unified DataFrame.
    
    Args:
        discharge_list: List of parsed discharge dictionaries
        
    Returns:
        DataFrame with unified data
    """
    if not discharge_list:
        logger.warning("No discharge data to process")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
    # Filter out None values
    valid_data = [d for d in discharge_list if d is not None]
    
    if not valid_data:
        logger.warning("No valid discharge data after filtering")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
    # Create DataFrame
    df = pd.DataFrame(valid_data)
    
    # Ensure all required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col in ['te_profile', 'ne_profile']:
                df[col] = [[] for _ in range(len(df))]
            else:
                df[col] = 0.0
                
    # Reorder columns
    df = df[REQUIRED_COLUMNS]
    
    logger.info(f"Processed {len(df)} discharges into unified dataset")
    return df


def generate_checksum(file_path: Path) -> str:
    """
    Generate SHA256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hex digest string
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        raise


def save_unified_dataset(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    generate_checksum_file: bool = True
) -> Tuple[Path, Optional[str]]:
    """
    Save unified dataset to CSV and generate checksum.
    
    Args:
        df: DataFrame to save
        output_path: Output path (defaults to OUTPUT_PATH)
        generate_checksum_file: Whether to generate checksum file
        
    Returns:
        Tuple of (output_path, checksum_string)
    """
    if output_path is None:
        output_path = OUTPUT_PATH
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved unified dataset to {output_path}")
    
    checksum = None
    if generate_checksum_file:
        checksum = generate_checksum(output_path)
        checksum_path = Path(str(output_path) + ".sha256")
        with open(checksum_path, "w") as f:
            f.write(checksum)
        logger.info(f"Generated checksum: {checksum}")
        
    return output_path, checksum


def main():
    """
    Main entry point for preprocessing module.
    Demonstrates the workflow for a sample discharge.
    """
    logger.info("Starting preprocessing module")
    
    # Sample data for demonstration
    sample_data = {
        'island_width': 0.05,
        'resonant_surface_density': 12.5,
        'tau_e': 0.12,
        'h98y2': 0.92,
        'q_min': 1.8,
        'q_max': 4.2,
        'te_profile': [1.0, 2.0, 3.0, 4.0, 5.0],
        'ne_profile': [0.5, 1.0, 1.5, 2.0, 2.5]
    }
    
    parsed = parse_discharge_data(sample_data, 123456)
    if parsed:
        df = process_multiple_discharges([parsed])
        path, checksum = save_unified_dataset(df)
        logger.info(f"Sample output saved to {path} with checksum {checksum}")
    else:
        logger.error("Failed to process sample data")


if __name__ == "__main__":
    main()