"""
Task T012f: Checksum Raw
Record computed SHA-256 checksum in `data/raw/checksums.json` with filename and hash.
Depends on T012 (download utility).
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path

# Setup logging for this module
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def main():
    """
    Main entry point for T012f.
    Computes SHA-256 checksum of downloaded raw data files and records them.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting T012f: Checksum Raw")
    
    # Define paths
    raw_data_dir = get_path("raw_data_dir")
    checksum_output_path = get_path("checksums_raw")
    
    # Ensure output directory exists
    checksum_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_data_dir}")
        logger.error("Please ensure T012 (download) has been completed successfully.")
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Find all files in the raw data directory
    files_to_checksum = []
    for ext in ["*.txt", "*.csv", "*.json", "*.zip", "*.tar.gz"]:
        files_to_checksum.extend(raw_data_dir.glob(ext))
    
    # Also include hidden files or files without extension if necessary
    # But typically ADReSS comes as specific archives or CSVs
    
    if not files_to_checksum:
        logger.warning(f"No files found in {raw_data_dir} to checksum.")
        # Create an empty checksum file or log error? 
        # Per task: "Record computed SHA-256 checksum". If no files, log warning and exit.
        # We will create an empty dict if no files found to avoid downstream errors, 
        # but log the warning.
        checksums_data = {}
    else:
        checksums_data = {}
        for file_path in files_to_checksum:
            try:
                file_hash = compute_sha256(file_path)
                checksums_data[file_path.name] = file_hash
                logger.info(f"Checksum computed for {file_path.name}: {file_hash}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path.name}: {e}")
                # Decide whether to fail or continue. 
                # For robustness, we continue but log error.
    
    # Save checksums to JSON
    try:
        with open(checksum_output_path, "w", encoding="utf-8") as f:
            json.dump(checksums_data, f, indent=2)
        logger.info(f"Checksums saved to {checksum_output_path}")
    except IOError as e:
        logger.error(f"Failed to write checksums to {checksum_output_path}: {e}")
        raise
    
    logger.info("T012f completed successfully.")

if __name__ == "__main__":
    main()
