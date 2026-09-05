"""
Download USPTO dataset from verified public source.

Primary Source: HuggingFace ChemBL USPTO Yield dataset.
Output: data/raw/uspto_raw.parquet
Checksum: data/results/download_checksum.txt
"""
import hashlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_SOURCE = "chembl/USPTO_yield"
FILE_NAME = "uspto_yield.parquet"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "uspto_raw.parquet"
CHECKSUM_DIR = Path("data/results")
CHECKSUM_FILE = CHECKSUM_DIR / "download_checksum.txt"
REPO_ID = "chembl/USPTO_yield"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_uspto_dataset() -> Path:
    """
    Download the USPTO dataset from HuggingFace.
    
    Returns:
        Path: Path to the downloaded parquet file.
        
    Raises:
        FileNotFoundError: If the download fails.
        Exception: If any other error occurs during download.
    """
    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKSUM_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading dataset from {REPO_ID}...")
    logger.info(f"Target file: {FILE_NAME}")
    
    try:
        # Use hf_hub_download to get the file
        # This handles authentication and streaming for large files
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILE_NAME,
            repo_type="dataset",
            cache_dir=None  # Download directly to current location logic if needed, but hf_hub_download returns local path
        )
        
        # Move the file to our output directory if it's not already there
        # hf_hub_download returns the path in cache, so we need to copy/move
        if downloaded_path != str(OUTPUT_FILE):
            import shutil
            shutil.copy2(downloaded_path, OUTPUT_FILE)
            logger.info(f"Copied downloaded file to {OUTPUT_FILE}")
        else:
            logger.info(f"File already at target location {OUTPUT_FILE}")
            
        # Verify the file exists and is not empty
        if not OUTPUT_FILE.exists():
            raise FileNotFoundError(f"Downloaded file not found at {OUTPUT_FILE}")
            
        if OUTPUT_FILE.stat().st_size == 0:
            raise FileNotFoundError(f"Downloaded file is empty at {OUTPUT_FILE}")
            
        logger.info(f"Download successful: {OUTPUT_FILE}")
        logger.info(f"File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")
        
        return OUTPUT_FILE
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        raise FileNotFoundError("No verified canonical data source available") from e

def write_checksum(file_path: Path) -> str:
    """Calculate and write checksum to file."""
    checksum = calculate_sha256(file_path)
    with open(CHECKSUM_FILE, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    logger.info(f"Checksum written to {CHECKSUM_FILE}: {checksum}")
    return checksum

def main():
    """Main entry point for the download script."""
    logger.info("Starting USPTO dataset download...")
    
    try:
        # Download the dataset
        output_path = download_uspto_dataset()
        
        # Calculate and write checksum
        checksum = write_checksum(output_path)
        
        logger.info("Download and checksum verification completed successfully.")
        logger.info(f"Output file: {output_path}")
        logger.info(f"Checksum: {checksum}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Critical error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
