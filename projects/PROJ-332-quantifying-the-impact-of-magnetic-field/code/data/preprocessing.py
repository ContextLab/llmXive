import logging
import numpy as np
import pandas as pd
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def align_time_series(time, *args):
    """
    Align multiple time-series arrays to the shortest common time base.
    
    Args:
        time: Time array (1D)
        *args: Data arrays to align (1D or 2D)
    
    Returns:
        Tuple of (aligned_time, aligned_data_1, aligned_data_2, ...)
    """
    min_len = min(len(arr) for arr in [time] + list(args))
    return tuple(arr[:min_len] for arr in [time] + list(args))

def extract_snapshot(df: pd.DataFrame, time_col: str, target_time: float, value_col: str) -> Optional[float]:
    """
    Extract the value at the closest time point to target_time.
    
    Args:
        df: DataFrame containing time series data
        time_col: Name of the time column
        target_time: Desired time point
        value_col: Name of the value column
    
    Returns:
        Value at closest time point, or None if data is empty
    """
    if df.empty:
        return None
    
    closest_idx = (df[time_col] - target_time).abs().idxmin()
    return df.loc[closest_idx, value_col]

def calculate_island_width(raw_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate island width from raw MDSplus data.
    
    Args:
        raw_data: Dictionary containing island width data or derivation inputs
    
    Returns:
        Island width in meters, or None if calculation fails
    """
    # If pre-calculated island width exists, use it
    if 'island_width' in raw_data and raw_data['island_width'] is not None:
        return float(raw_data['island_width'])
    
    # Otherwise, attempt derivation using Rutherford equation
    # This function is a placeholder for the actual derivation logic
    # The real implementation would use local_magnetic_shear, q_profile, Bt_field
    logger.warning("Pre-calculated island width missing, derivation not fully implemented in this context.")
    return None

def determine_confinement_mode(h98y2: Optional[float]) -> str:
    """
    Determine confinement mode based on H-factor.
    
    Args:
        h98y2: H98(y,2) confinement enhancement factor
    
    Returns:
        'H-mode' if h98y2 >= 0.85, else 'L-mode'
    """
    if h98y2 is None or h98y2 < 0.85:
        return 'L-mode'
    return 'H-mode'

def parse_discharge_data(raw_data: Dict[str, Any], discharge_id: int) -> Dict[str, Any]:
    """
    Parse raw MDSplus data into a structured dictionary.
    
    Args:
        raw_data: Raw data dictionary from MDSplus
        discharge_id: Discharge identifier
    
    Returns:
        Parsed data dictionary with standardized keys
    """
    parsed = {
        'discharge_id': discharge_id,
        'island_width': None,
        'tau_e': None,
        'h98y2': None,
        'confinement_mode': 'L-mode',
        'te_profile': None,
        'ne_profile': None,
        'raw_data': raw_data
    }
    
    # Extract island width
    parsed['island_width'] = calculate_island_width(raw_data)
    
    # Extract tau_e (energy confinement time)
    if 'tau_e' in raw_data and raw_data['tau_e'] is not None:
        parsed['tau_e'] = float(raw_data['tau_e'])
    
    # Extract h98y2
    if 'h98y2' in raw_data and raw_data['h98y2'] is not None:
        parsed['h98y2'] = float(raw_data['h98y2'])
        parsed['confinement_mode'] = determine_confinement_mode(parsed['h98y2'])
    
    # Extract profiles if available
    if 'te_profile' in raw_data:
        parsed['te_profile'] = raw_data['te_profile']
    if 'ne_profile' in raw_data:
        parsed['ne_profile'] = raw_data['ne_profile']
    
    return parsed

def process_multiple_discharges(parsed_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of parsed discharge dictionaries into a DataFrame.
    
    Args:
        parsed_list: List of parsed discharge dictionaries
    
    Returns:
        DataFrame with standardized columns
    """
    # Filter out discharges with missing critical data
    valid_discharges = [
        d for d in parsed_list 
        if d['island_width'] is not None and d['tau_e'] is not None
    ]
    
    if not valid_discharges:
        logger.warning("No valid discharges found with both island_width and tau_e.")
        return pd.DataFrame()
    
    # Create DataFrame
    data_rows = []
    for d in valid_discharges:
        row = {
            'discharge_id': d['discharge_id'],
            'island_width': d['island_width'],
            'tau_e': d['tau_e'],
            'confinement_mode': d['confinement_mode'],
            'h98y2': d['h98y2']
        }
        data_rows.append(row)
    
    return pd.DataFrame(data_rows)

def validate_parsed_data(df: pd.DataFrame) -> bool:
    """
    Validate the parsed DataFrame against basic requirements.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        True if valid, False otherwise
    """
    if df.empty:
        logger.error("DataFrame is empty.")
        return False
    
    required_cols = ['discharge_id', 'island_width', 'tau_e', 'confinement_mode', 'h98y2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for NaN values in critical columns
    critical_cols = ['discharge_id', 'island_width', 'tau_e', 'h98y2']
    for col in critical_cols:
        if df[col].isna().any():
            logger.warning(f"Column {col} contains NaN values.")
    
    return True

def generate_checksum(df: pd.DataFrame) -> str:
    """
    Generate a SHA-256 checksum for the DataFrame content.
    
    Args:
        df: DataFrame to checksum
    
    Returns:
        Hex string of the SHA-256 hash
    """
    # Convert DataFrame to bytes for hashing
    csv_content = df.to_csv(index=False).encode('utf-8')
    return hashlib.sha256(csv_content).hexdigest()

def save_unified_dataset(df: pd.DataFrame, output_path: str) -> Tuple[str, str]:
    """
    Save the unified dataset to CSV and generate a checksum.
    
    Args:
        df: DataFrame to save
        output_path: Path to the output CSV file
    
    Returns:
        Tuple of (file_path, checksum)
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    checksum = generate_checksum(df)
    
    logger.info(f"Saved unified dataset to {output_file} with checksum: {checksum}")
    return str(output_file), checksum

def main():
    """
    Main entry point for the preprocessing module.
    This function is intended to be called by the pipeline orchestrator.
    """
    logger.info("Preprocessing module initialized.")
    # Note: Actual data loading and processing is handled by the pipeline
    # This function serves as a module entry point for testing or direct invocation.

if __name__ == "__main__":
    main()
