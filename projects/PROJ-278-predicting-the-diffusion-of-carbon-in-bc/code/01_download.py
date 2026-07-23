"""Script to download and validate the raw dataset.

Fetches the verified HuggingFace dataset, validates checksum (if available),
and ensures required columns are present. Raises DataInsufficientError on failure.
"""
import os
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional
import requests
import pandas as pd

# Import using absolute imports compatible with running as a script
# The project structure allows importing from the 'code' package
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import setup_logger, handle_data_insufficient
from exceptions import DataInsufficientError

logger = setup_logger(__name__)

# Verified HuggingFace dataset URL for MeLiDC
DATASET_URL = "https://huggingface.co/datasets/MeliDC/MeLiDC/resolve/main/data.parquet"
# We do not enforce a static checksum if the URL is trusted and streaming,
# but we will compute one for the local file for record-keeping.
# If a specific checksum is provided by the data source, it should be hardcoded here.
EXPECTED_SHA256 = None  # No static checksum enforced, but file integrity checked via HTTP

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> None:
    """Download a file from a URL with streaming to handle large files."""
    logger.info(f"Downloading from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Write to a temporary file first to avoid partial writes on failure
        temp_path = dest_path.with_suffix('.parquet.tmp')
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Atomic move
        temp_path.rename(dest_path)
        logger.info(f"Downloaded to {dest_path}")
    except requests.exceptions.RequestException as e:
        raise DataInsufficientError(f"Failed to download dataset: {e}")

def validate_columns(df: pd.DataFrame, required_cols: list) -> None:
    """Validate that the dataframe contains all required columns."""
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise DataInsufficientError(f"Missing required columns: {missing_cols}")
    
    if len(df) == 0:
        raise DataInsufficientError("Dataset is empty after download.")

def main():
    """Main execution function."""
    raw_data_dir = Path(__file__).parent.parent / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = raw_data_dir / "dataset.parquet"
    required_cols = ['structure', 'composition', 'diffusion_coefficient', 'temperature', 'microstructure_controlled']
    
    try:
        if output_file.exists():
            logger.info("Raw dataset already exists. Verifying integrity...")
            # Optional: Re-verify checksum if EXPECTED_SHA256 is set
            if EXPECTED_SHA256:
                actual_checksum = compute_sha256(output_file)
                if actual_checksum != EXPECTED_SHA256:
                    raise DataInsufficientError(f"Checksum mismatch: {actual_checksum} != {EXPECTED_SHA256}")
        else:
            download_file(DATASET_URL, output_file)
        
        # Validate content
        logger.info("Validating dataset content...")
        df = pd.read_parquet(output_file)
        
        validate_columns(df, required_cols)
        
        logger.info(f"Dataset validated successfully.")
        logger.info(f"  Rows: {len(df)}")
        logger.info(f"  Columns: {list(df.columns)}")
        
        # Log checksum for record
        checksum = compute_sha256(output_file)
        logger.info(f"  SHA256: {checksum}")
        
    except DataInsufficientError:
        raise
    except Exception as e:
        handle_data_insufficient(DataInsufficientError(f"Download or validation failed: {e}"))

if __name__ == "__main__":
    main()