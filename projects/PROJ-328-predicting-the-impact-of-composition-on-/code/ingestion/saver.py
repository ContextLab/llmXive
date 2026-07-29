"""
Data Saver Module for Solder Hardness Project.

Handles saving raw data with checksums and validated datasets to disk.
"""
import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from config import get_data_raw_dir, get_data_processed_dir, get_composition_sum_threshold
from seed import init_reproducibility
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)

# Constants
RAW_DATA_FILENAME = "solder_hardness_raw.csv"
PROCESSED_DATA_FILENAME = "solder_hardness_validated.csv"
CHECKSUMS_FILENAME = "checksums.txt"

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        MD5 hex digest string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_raw_data_with_checksums(df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
    """Save raw data to CSV and generate checksums.
    
    Args:
        df: DataFrame containing raw solder composition data.
        output_dir: Directory to save files. Defaults to raw data directory.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        DataValidationError: If DataFrame is empty or None.
    """
    if df is None or df.empty:
        raise DataValidationError("Cannot save empty or None DataFrame.")
    
    output_dir = output_dir or get_data_raw_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / RAW_DATA_FILENAME
    checksum_path = output_dir / CHECKSUMS_FILENAME
    
    # Save to CSV
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved raw data to {csv_path}")
    
    # Calculate and save checksum
    checksum = calculate_md5(csv_path)
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {RAW_DATA_FILENAME}\n")
    
    logger.info(f"Generated checksum for {RAW_DATA_FILENAME}: {checksum}")
    return csv_path

def save_validated_data(df: pd.DataFrame, output_dir: Optional[Path] = None) -> Path:
    """Save validated dataset to CSV.
    
    This function takes the validated DataFrame (post-cleaning, filtering, and validation)
    and saves it to the processed data directory.
    
    Args:
        df: DataFrame containing validated solder composition data.
        output_dir: Directory to save file. Defaults to processed data directory.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        DataValidationError: If DataFrame is empty or None.
    """
    if df is None or df.empty:
        raise DataValidationError("Cannot save empty or None validated DataFrame.")
    
    output_dir = output_dir or get_data_processed_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / PROCESSED_DATA_FILENAME
    
    # Ensure all composition columns are numeric and sum to ~1.0
    composition_cols = [col for col in df.columns if col.startswith('element_') or col in ['Sn', 'Pb', 'Ag', 'Cu', 'Bi', 'In', 'Sb', 'Zn', 'Ni', 'Fe', 'Au', 'Pd', 'Re']]
    
    # Log summary statistics
    logger.info(f"Validated dataset shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated data to {output_path}")
    
    # Log checksum for validation record
    checksum = calculate_md5(output_path)
    logger.info(f"Checksum for {PROCESSED_DATA_FILENAME}: {checksum}")
    
    return output_path

def main():
    """Main entry point for testing the saver module."""
    init_reproducibility()
    
    # Example usage: Load a dummy dataset for demonstration
    # In real execution, this would be called by the pipeline runner
    # with data from the validator module.
    
    logger.info("Saver module loaded successfully.")
    logger.info(f"Raw data directory: {get_data_raw_dir()}")
    logger.info(f"Processed data directory: {get_data_processed_dir()}")
    
    # Example DataFrame creation (for module testing only)
    # In production, this DataFrame comes from validator.py
    try:
        sample_data = {
            'id': [1, 2, 3],
            'source': ['NIST', 'Materials Project', 'Literature'],
            'Sn': [0.95, 0.60, 0.99],
            'Ag': [0.03, 0.05, 0.00],
            'Cu': [0.02, 0.35, 0.01],
            'hardness_hv': [60.5, 75.2, 15.0]
        }
        sample_df = pd.DataFrame(sample_data)
        
        # Save as raw
        raw_path = save_raw_data_with_checksums(sample_df)
        logger.info(f"Sample raw data saved to: {raw_path}")
        
        # Save as validated
        validated_path = save_validated_data(sample_df)
        logger.info(f"Sample validated data saved to: {validated_path}")
        
    except Exception as e:
        logger.error(f"Error during sample save: {e}")
        raise

if __name__ == "__main__":
    main()