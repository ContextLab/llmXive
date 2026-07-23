"""Script to download and validate the raw dataset."""
import os
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional
import requests
import pandas as pd

from .logging_config import setup_logger, handle_data_insufficient
from .exceptions import DataInsufficientError

logger = setup_logger(__name__)

# Verified HuggingFace dataset URL (placeholder for real URL)
# In a real scenario, this would be the specific dataset ID or URL
DATASET_URL = "https://huggingface.co/datasets/example/carbon-diffusion-bcc/resolve/main/data.parquet"
EXPECTED_SHA256 = "placeholder_checksum" # Replace with actual checksum

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> None:
    """Download a file from a URL."""
    logger.info(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Downloaded to {dest_path}")

def main():
    """Main execution function."""
    raw_data_dir = Path(__file__).parent.parent / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = raw_data_dir / "dataset.parquet"
    
    try:
        if output_file.exists():
            logger.info("Raw dataset already exists. Skipping download.")
            # Optionally verify checksum here
        else:
            download_file(DATASET_URL, output_file)
        
        # Verify checksum (if real checksum is known)
        # actual_checksum = compute_sha256(output_file)
        # if actual_checksum != EXPECTED_SHA256:
        #     raise DataInsufficientError(f"Checksum mismatch: {actual_checksum} != {EXPECTED_SHA256}")
        
        # Validate columns
        df = pd.read_parquet(output_file)
        required_cols = ['structure', 'composition', 'diffusion_coefficient', 'temperature', 'microstructure_controlled']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            raise DataInsufficientError(f"Missing required columns: {missing_cols}")
        
        if len(df) == 0:
            raise DataInsufficientError("Dataset is empty.")
        
        logger.info(f"Dataset validated. Rows: {len(df)}, Columns: {list(df.columns)}")
        
    except Exception as e:
        handle_data_insufficient(DataInsufficientError(f"Download or validation failed: {e}"))

if __name__ == "__main__":
    main()
