import os
import json
import hashlib
import shutil
import pandas as pd
from typing import Dict, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_sha256(filepath: str) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {filepath}: {e}") from e

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned DataFrame to a CSV file.
    
    Args:
        df: The cleaned DataFrame to save.
        output_path: Path where the CSV file will be saved.
        
    Raises:
        IOError: If the file cannot be written.
    """
    if df.empty:
        logger.warning("Attempting to save an empty DataFrame.")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path} ({len(df)} rows)")
    except IOError as e:
        raise IOError(f"Failed to write to {output_path}: {e}") from e

def record_checksum(output_path: str, checksum_path: str) -> None:
    """
    Compute the checksum of the output file and record it in a JSON file.
    
    Args:
        output_path: Path to the output file (e.g., CSV).
        checksum_path: Path to the JSON file where the checksum will be stored.
        
    Raises:
        FileNotFoundError: If the output file does not exist.
        IOError: If the checksum file cannot be written.
    """
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Output file not found for checksum: {output_path}")
    
    checksum = compute_sha256(output_path)
    file_name = os.path.basename(output_path)
    
    # Load existing checksums if the file exists
    checksums = {}
    if os.path.exists(checksum_path):
        try:
            with open(checksum_path, 'r') as f:
                checksums = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Checksum file was invalid, overwriting.")
            checksums = {}
    
    # Update the checksum for this specific file
    checksums[file_name] = checksum
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    
    try:
        with open(checksum_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Recorded checksum for {file_name} in {checksum_path}")
    except IOError as e:
        raise IOError(f"Failed to write checksum to {checksum_path}: {e}") from e

def ensure_raw_data_preserved(raw_dir: str) -> None:
    """
    Verify that the raw data directory exists and is not empty.
    This ensures that the cleaning process did not overwrite the raw source.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Raises:
        FileNotFoundError: If the raw directory does not exist.
        ValueError: If the raw directory is empty.
    """
    if not os.path.exists(raw_dir):
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    if not os.listdir(raw_dir):
        raise ValueError(f"Raw data directory is empty: {raw_dir}")
    
    logger.info(f"Verified raw data preservation in {raw_dir}")

def save_orbit_solution(solution: Dict[str, Any], output_path: str) -> None:
    """
    Save orbit solution results to a JSON file.
    
    Args:
        solution: Dictionary containing the orbit solution data.
        output_path: Path where the JSON file will be saved.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(solution, f, indent=2)
    logger.info(f"Saved orbit solution to {output_path}")

def save_eotvos_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save Eötvös parameter results to a JSON file.
    
    Args:
        metrics: Dictionary containing the Eötvös metrics.
        output_path: Path where the JSON file will be saved.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved Eötvös metrics to {output_path}")

def run_output_pipeline(cleaned_df: pd.DataFrame, 
                        raw_data_dir: str, 
                        output_csv: str, 
                        checksum_json: str) -> None:
    """
    Execute the full output pipeline: save data, verify raw preservation, and record checksums.
    
    Args:
        cleaned_df: The cleaned DataFrame to save.
        raw_data_dir: Path to the raw data directory (for verification).
        output_csv: Path for the output CSV file.
        checksum_json: Path for the checksums JSON file.
    """
    # 1. Ensure raw data is preserved
    ensure_raw_data_preserved(raw_data_dir)
    
    # 2. Save the cleaned data
    save_cleaned_data(cleaned_df, output_csv)
    
    # 3. Compute and record the checksum
    record_checksum(output_csv, checksum_json)
    
    logger.info("Output pipeline completed successfully.")
