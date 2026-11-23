"""
Saver module for ingestion pipeline.
Handles saving raw and validated data with checksums.
"""
import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging_config import get_logger
from config import get_data_processed_dir, get_data_raw_dir, get_data_outputs_dir

logger = get_logger(__name__)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_raw_data_with_checksums(df: Any, filename: str = "solder_hardness_raw.csv") -> Path:
    """
    Save raw data to data/raw/ and record checksum in data/checksums.txt.
    
    Args:
        df: Pandas DataFrame containing raw data
        filename: Output filename
        
    Returns:
        Path to the saved file
    """
    raw_dir = get_data_raw_dir()
    output_path = raw_dir / filename
    
    # Ensure directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")
    
    # Calculate checksum
    checksum = calculate_md5(output_path)
    
    # Update checksums file
    checksums_file = raw_dir.parent / "checksums.txt"
    with open(checksums_file, "a") as f:
        f.write(f"{filename}:{checksum}\n")
    
    logger.info(f"Added checksum for {filename}: {checksum}")
    return output_path

def save_validated_data(df: Any, filename: str = "solder_hardness_validated.csv") -> Path:
    """
    Save validated data to data/processed/ and record checksum in data/checksums.txt.
    
    Args:
        df: Pandas DataFrame containing validated data
        filename: Output filename
        
    Returns:
        Path to the saved file
    """
    processed_dir = get_data_processed_dir()
    output_path = processed_dir / filename
    
    # Ensure directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated data to {output_path}")
    
    # Calculate checksum
    checksum = calculate_md5(output_path)
    
    # Update checksums file
    checksums_file = processed_dir.parent / "checksums.txt"
    with open(checksums_file, "a") as f:
        f.write(f"{filename}:{checksum}\n")
    
    logger.info(f"Added checksum for {filename}: {checksum}")
    return output_path

def main():
    """
    Main entry point for the saver module.
    This function is typically called by the pipeline runner after validation.
    """
    logger.info("Saver module initialized. Use save_validated_data() to save processed data.")

if __name__ == "__main__":
    main()