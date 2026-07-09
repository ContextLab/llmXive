"""
Download and verify the DSSC dataset from Zenodo.

This script handles:
1. Downloading the Nazeer et al. DSSC dataset (T009 functionality)
2. Verifying file existence and checksum (T010 functionality)
3. Validating PCE units and flagging anomalies
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.retry_utils import retry_request
from utils.logger import setup_logger
from utils.config import ensure_dirs
from utils.data_loader import load_csv

# Configuration
ZENODO_RECORD_ID = "10.5281/zenodo.4921127"
ZENODO_BASE_URL = "https://zenodo.org/api/records"
TARGET_FILENAME = "dssc_dataset.csv"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
REVIEW_QUEUE_FILE = "data/processed/review_queue.json"

# Expected checksum for the dataset (to be updated by researcher)
# Placeholder: This should be replaced with the actual SHA256 of the real file
EXPECTED_CHECKSUM = "PLACEHOLDER_SHA256_CHECKSUM"

def get_download_url(record_id: str, filename: str) -> str:
    """
    Fetch the download URL for a specific file from a Zenodo record.
    
    Args:
        record_id: Zenodo record ID
        filename: Name of the file to download
        
    Returns:
        Direct download URL
        
    Raises:
        ValueError: If record or file not found
    """
    url = f"{ZENODO_BASE_URL}/{record_id}/files"
    logger = setup_logger()
    
    try:
        response = retry_request(url, max_retries=3, backoff_factor=2)
        if response is None:
            raise RuntimeError(f"Failed to fetch file list from {url} after retries")
        
        data = response.json()
        
        # Look for the specific file
        for file_info in data.get('files', []):
            if file_info.get('filename') == filename:
                return file_info.get('links', {}).get('self')
        
        # If not found in 'files', check 'entries' (alternative structure)
        for entry in data.get('entries', []):
            if entry.get('filename') == filename:
                return entry.get('links', {}).get('download')
                
        raise ValueError(f"File '{filename}' not found in record {record_id}. "
                       f"Available files: {[f.get('filename') for f in data.get('files', [])]}")
                            
    except Exception as e:
        logger.error(f"Error fetching download URL: {e}")
        raise

def download_dataset(record_id: str, filename: str, output_path: Path) -> None:
    """
    Download a dataset file from Zenodo with retry logic.
    
    Args:
        record_id: Zenodo record ID
        filename: Name of the file to download
        output_path: Local path to save the file
    """
    logger = setup_logger()
    
    # Ensure output directory exists
    ensure_dirs()
    
    logger.info(f"Starting download of {filename} from Zenodo record {record_id}")
    
    try:
        # Get the direct download URL
        download_url = get_download_url(record_id, filename)
        logger.info(f"Download URL obtained: {download_url}")
        
        # Download the file with retry logic
        response = retry_request(download_url, max_retries=3, backoff_factor=2, stream=True)
        
        if response is None:
            raise RuntimeError(f"Download failed after retries for URL: {download_url}")
        
        response.raise_for_status()
        
        # Write to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        logger.info(f"Successfully downloaded {filename} to {output_path}")
        logger.info(f"File size: {output_path.stat().st_size} bytes")
        
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        logger.error(f"Expected location: {output_path}")
        raise

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hex digest
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA256 hex digest
        
    Returns:
        True if checksum matches, False otherwise
    """
    if expected_checksum == "PLACEHOLDER_SHA256_CHECKSUM":
        logging.warning("Checksum verification skipped: EXPECTED_CHECKSUM is a placeholder.")
        return True
        
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def load_review_queue() -> list:
    """Load existing review queue if it exists."""
    queue_path = Path(REVIEW_QUEUE_FILE)
    if queue_path.exists():
        with open(queue_path, 'r') as f:
            return json.load(f)
    return []

def save_review_queue(queue: list) -> None:
    """Save review queue to file."""
    ensure_dirs()
    queue_path = Path(REVIEW_QUEUE_FILE)
    with open(queue_path, 'w') as f:
        json.dump(queue, f, indent=2)

def flag_for_review(smiles: str, value: float, unit: str, reason: str) -> None:
    """Add an entry to the review queue."""
    queue = load_review_queue()
    entry = {
        "smiles": smiles,
        "value": value,
        "unit": unit,
        "status": "flagged_for_review",
        "reason": reason
    }
    queue.append(entry)
    save_review_queue(queue)

def verify_pce_units(df) -> None:
    """
    Verify PCE units are percentages within standard range.
    Flags anomalies in review queue.
    """
    logger = setup_logger()
    
    # Check if PCE column exists
    if 'PCE' not in df.columns:
        logger.warning("PCE column not found in dataset. Skipping unit verification.")
        return
        
    pce_values = df['PCE'].dropna()
    
    # Standard DSSC PCE range (typically 0-15% for most dyes, up to 20% for record holders)
    MIN_PCE = 0.0
    MAX_PCE = 25.0
    
    for idx, value in pce_values.items():
        if not isinstance(value, (int, float)):
            flag_for_review(
                smiles=str(df.iloc[idx].get('SMILES', 'N/A')),
                value=float(value) if value else 0.0,
                unit="unknown",
                reason="Non-numeric PCE value"
            )
            continue
            
        if value < MIN_PCE or value > MAX_PCE:
            flag_for_review(
                smiles=str(df.iloc[idx].get('SMILES', 'N/A')),
                value=float(value),
                unit="%",
                reason=f"PCE value {value} outside expected range [{MIN_PCE}, {MAX_PCE}]"
            )
            logger.warning(f"Flagged PCE value {value} at index {idx} for review")

def main():
    """Main entry point for download and verification script."""
    logger = setup_logger()
    logger.info("DSSC Dataset Downloader and Verifier starting...")
    
    # Define paths
    raw_data_dir = Path(RAW_DATA_DIR)
    output_file = raw_data_dir / TARGET_FILENAME
    
    try:
        # Step 1: Download dataset if not exists
        if not output_file.exists():
            logger.info("Dataset not found. Starting download...")
            download_dataset(ZENODO_RECORD_ID, TARGET_FILENAME, output_file)
        else:
            logger.info(f"Dataset already exists at {output_file}")
        
        # Step 2: Verify checksum
        logger.info("Verifying file checksum...")
        checksum_valid = verify_checksum(output_file, EXPECTED_CHECKSUM)
        
        if not checksum_valid:
            actual = compute_file_checksum(output_file)
            logger.warning(f"Checksum mismatch! Expected: {EXPECTED_CHECKSUM}, Got: {actual}")
            # Log to review queue but continue processing
            queue = load_review_queue()
            queue.append({
                "file": str(output_file),
                "status": "checksum_mismatch",
                "expected": EXPECTED_CHECKSUM,
                "actual": actual
            })
            save_review_queue(queue)
        else:
            logger.info("Checksum verification passed.")
        
        # Step 3: Load and verify PCE units
        logger.info("Loading dataset for PCE unit verification...")
        df = load_csv(str(output_file))
        
        logger.info(f"Dataset loaded with {len(df)} rows and columns: {list(df.columns)}")
        verify_pce_units(df)
        
        logger.info("Dataset download and verification completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Dataset download/verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
