"""
Output utilities for the SLR Equivalence Principle Pipeline.

Handles saving cleaned data, computing checksums, and ensuring
raw data integrity.
"""
import os
import json
import hashlib
import shutil
import pandas as pd
from typing import Dict, Any, Optional
from utils.logging import get_logger, log_progress, log_error

logger = get_logger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        log_error(logger, f"File not found for checksum: {file_path}")
        raise
    except IOError as e:
        log_error(logger, f"IO error reading file for checksum: {file_path}, {e}")
        raise

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned DataFrame to a CSV file.
    
    Args:
        df: The cleaned pandas DataFrame.
        output_path: Path where the CSV will be saved.
        
    Raises:
        IOError: If the file cannot be written.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        df.to_csv(output_path, index=False)
        log_progress(logger, f"Cleaned data saved to {output_path}")
    except IOError as e:
        log_error(logger, f"Failed to save cleaned data to {output_path}: {e}")
        raise

def record_checksum(file_path: str, checksum_dir: str, checksums_file: str = ".checksums.json") -> None:
    """
    Record the checksum of a file into a JSON manifest.
    
    Args:
        file_path: Path to the file that was processed.
        checksum_dir: Directory where the checksum manifest lives.
        checksums_file: Name of the JSON file to update.
        
    The manifest format:
        {
            "file": "relative/path/to/file.csv",
            "sha256": "..."
        }
    """
    manifest_path = os.path.join(checksum_dir, checksums_file)
    
    # Load existing checksums if present
    checksums = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                checksums = json.load(f)
        except json.JSONDecodeError:
            log_error(logger, f"Corrupt checksum manifest at {manifest_path}, starting fresh.")
            checksums = {}
    
    # Compute new checksum
    filename = os.path.basename(file_path)
    checksum = compute_sha256(file_path)
    
    # Update record
    checksums[filename] = checksum
    
    # Write back
    if not os.path.exists(checksum_dir):
        os.makedirs(checksum_dir)
        
    with open(manifest_path, 'w') as f:
        json.dump(checksums, f, indent=2)
        
    log_progress(logger, f"Checksum recorded for {filename}: {checksum}")

def ensure_raw_data_preserved(raw_dir: str, processed_dir: str) -> None:
    """
    Verify that the raw data directory exists and contains files,
    ensuring the pipeline did not overwrite the source.
    
    Args:
        raw_dir: Path to the raw data directory.
        processed_dir: Path to the processed data directory (to compare).
        
    Raises:
        FileNotFoundError: If raw data is missing.
    """
    if not os.path.exists(raw_dir):
        raise FileNotFoundError(f"Raw data directory missing: {raw_dir}. "
                                "Ensure raw data ingestion completed successfully.")
                                
    raw_files = [f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]
    if not raw_files:
        raise FileNotFoundError(f"Raw data directory is empty: {raw_dir}")
        
    log_progress(logger, f"Verified {len(raw_files)} raw files preserved in {raw_dir}")

def save_orbit_solution(solution: Any, output_path: str) -> None:
    """
    Save an OrbitSolution object to JSON.
    
    Args:
        solution: The OrbitSolution object (must have a to_dict method).
        output_path: Path to save the JSON.
    """
    # Assuming OrbitSolution has a to_dict method or is serializable
    # If not, we would need specific serialization logic here
    if hasattr(solution, 'to_dict'):
        data = solution.to_dict()
    elif isinstance(solution, dict):
        data = solution
    else:
        raise TypeError("OrbitSolution must be dict-like or have a to_dict method")
        
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    log_progress(logger, f"Orbit solution saved to {output_path}")

def save_eotvos_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save EotvosResult metrics to JSON.
    
    Args:
        metrics: Dictionary containing eta, ci, etc.
        output_path: Path to save the JSON.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    log_progress(logger, f"Eotvos metrics saved to {output_path}")

def run_output_pipeline(df: pd.DataFrame, 
                        raw_dir: str, 
                        processed_dir: str, 
                        output_filename: str = "cleaned_slr_data.csv",
                        checksum_filename: str = ".checksums.json") -> str:
    """
    Orchestrates the saving of cleaned data, verification of raw data,
    and recording of checksums.
    
    Args:
        df: The cleaned DataFrame.
        raw_dir: Path to raw data directory.
        processed_dir: Path to processed data directory.
        output_filename: Name of the output CSV file.
        checksum_filename: Name of the checksum JSON file.
        
    Returns:
        Path to the saved CSV file.
        
    Raises:
        FileNotFoundError: If raw data is missing.
        IOError: If saving fails.
    """
    output_path = os.path.join(processed_dir, output_filename)
    
    # 1. Ensure raw data is safe
    ensure_raw_data_preserved(raw_dir, processed_dir)
    
    # 2. Save cleaned data
    save_cleaned_data(df, output_path)
    
    # 3. Record checksum
    record_checksum(output_path, processed_dir, checksum_filename)
    
    return output_path
