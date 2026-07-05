"""
Data Ingestion Module for NLCD Colorado Subset.

Downloads high-resolution NLCD 30m data for Colorado from a verified HuggingFace dataset,
validates the file using checksums, and applies retry logic for robustness.
"""
import os
import sys
import hashlib
import time
import logging
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).resolve().parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

import requests
from tqdm import tqdm

from config import (
    NLCD_HF_DATASET_ID,
    NLCD_HF_FILENAME,
    NLCD_EXPECTED_CHECKSUM,
    DATA_RAW_DIR,
    LOG_LEVEL,
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
)
from utils import setup_logging, get_logger, checksum_file, retry_with_backoff, RetryError

# Initialize logging
logger = get_logger(__name__)

# Constants
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for download
TIMEOUT = 60  # seconds per request chunk

def download_with_progress(url: str, dest_path: Path, filename: str) -> None:
    """
    Downloads a file from a URL with a progress bar.
    
    Args:
        url: The source URL.
        dest_path: The directory to save the file.
        filename: The name of the file to save.
    """
    dest_path.mkdir(parents=True, exist_ok=True)
    full_path = dest_path / filename
    
    logger.info(f"Downloading {filename} from {url}...")
    
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(full_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
        logger.info(f"Download complete: {full_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download: {e}")
        raise

def verify_download(filepath: Path, expected_checksum: str) -> bool:
    """
    Verifies the downloaded file against the expected SHA256 checksum.
    
    Args:
        filepath: Path to the downloaded file.
        expected_checksum: The expected SHA256 hex string.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    if not filepath.exists():
        logger.error(f"File not found for verification: {filepath}")
        return False
        
    actual_checksum = checksum_file(filepath)
    
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified successfully for {filepath.name}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {filepath.name}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )
        return False

@retry_with_backoff(max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY)
def run_ingestion() -> str:
    """
    Orchestrates the download, retry logic, and verification of the NLCD dataset.
    
    Returns:
        The path to the verified file.
        
    Raises:
        RetryError: If download or verification fails after all retries.
    """
    # Construct URL
    # HuggingFace dataset download URL pattern:
    # https://huggingface.co/datasets/{repo_id}/resolve/main/{filename}
    url = f"https://huggingface.co/datasets/{NLCD_HF_DATASET_ID}/resolve/main/{NLCD_HF_FILENAME}"
    
    dest_dir = Path(DATA_RAW_DIR)
    filename = NLCD_HF_FILENAME
    dest_path = dest_dir / filename
    
    # Step 1: Download
    try:
        download_with_progress(url, dest_dir, filename)
    except Exception as e:
        logger.warning(f"Download failed: {e}. Retrying...")
        raise RetryError(f"Download failed: {e}") from e
        
    # Step 2: Verify
    if not verify_download(dest_path, NLCD_EXPECTED_CHECKSUM):
        logger.warning("Verification failed. Removing corrupted file and retrying...")
        if dest_path.exists():
            dest_path.unlink()
        raise RetryError("Checksum verification failed")
        
    logger.info("Ingestion completed successfully.")
    return str(dest_path)

def main():
    """Entry point for the ingestion script."""
    setup_logging(level=LOG_LEVEL)
    logger.info("Starting NLCD Data Ingestion Pipeline...")
    
    try:
        output_path = run_ingestion()
        print(f"SUCCESS: Data ingested to {output_path}")
    except RetryError as e:
        logger.critical(f"Ingestion pipeline failed after retries: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
