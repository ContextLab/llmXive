"""
Fetch experimental barrier dataset from Zenodo.

This script implements FR-001: Data Fetching and Verification.
It retrieves the dataset using the Zenodo ID defined in config.py,
verifies the checksum, and ensures the output file exists in data/raw/.
"""
import hashlib
import logging
import os
import sys
import tarfile
import tempfile
from pathlib import Path

import requests

# Import the Zenodo ID from config (set by T004a)
# If T004a failed to set this, this import will fail or the value will be empty,
# triggering the required failure mode.
try:
    from config import ZENODO_ID
except ImportError:
    # Fallback if config is not in path (should not happen in normal execution)
    sys.path.insert(0, str(Path(__file__).parent))
    from config import ZENODO_ID

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "verification.log"

def setup_logger():
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def compute_sha256(filepath):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, dest_path, logger):
    """Download a file from URL with progress logging."""
    logger.info(f"Downloading from {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Progress: {percent:.1f}%")
        logger.info(f"Download complete: {dest_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False

def verify_checksum(filepath, expected_checksum, logger):
    """Verify file checksum."""
    if not expected_checksum:
        logger.warning("No expected checksum provided; skipping verification.")
        return True
    actual_checksum = compute_sha256(filepath)
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verification passed: {actual_checksum}")
        return True
    else:
        logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

def extract_tarball(tar_path, dest_dir, logger):
    """Extract tarball to destination directory."""
    logger.info(f"Extracting {tar_path} to {dest_dir}")
    try:
        with tarfile.open(tar_path, 'r:*') as tar:
            tar.extractall(path=dest_dir)
        logger.info("Extraction complete.")
        return True
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False

def convert_to_csv(tarball_path, output_csv_path, logger):
    """
    Extract CSV from the tarball if it's not already a CSV.
    For Zenodo datasets that are direct CSVs, this might just be a rename/copy.
    For this implementation, we assume the tarball contains a CSV or we look for it.
    """
    logger.info(f"Processing tarball {tarball_path} to find CSV for {output_csv_path}")
    
    # If the input is already a CSV (some Zenodo records allow direct download), handle it
    if tarball_path.endswith('.csv'):
        import shutil
        shutil.copy(tarball_path, output_csv_path)
        logger.info(f"Copied CSV directly to {output_csv_path}")
        return True

    # Otherwise, assume it's a tarball and look for the CSV inside
    try:
        with tarfile.open(tarball_path, 'r:*') as tar:
            members = tar.getnames()
            csv_member = None
            for member in members:
                if member.endswith('.csv'):
                    csv_member = member
                    break
            
            if csv_member:
                logger.info(f"Found CSV inside tarball: {csv_member}")
                with tar.extractfile(csv_member) as src:
                    with open(output_csv_path, 'wb') as dst:
                        dst.write(src.read())
                logger.info(f"Extracted CSV to {output_csv_path}")
                return True
            else:
                logger.error("No CSV file found inside the tarball.")
                return False
    except Exception as e:
        logger.error(f"Error processing tarball: {e}")
        return False

def fetch_and_verify_data(logger):
    """Main logic to fetch and verify data."""
    if not ZENODO_ID:
        logger.error("ZENODO_ID is empty. Cannot fetch data.")
        return False

    # Construct Zenodo API URL
    # Zenodo API endpoint for file download
    # Format: https://zenodo.org/api/files/{record_id}/{filename}
    # However, often the direct download link is: https://zenodo.org/record/{id}/files/{filename}
    # We need to find the filename. Let's try to get the record metadata first.
    
    api_url = f"https://zenodo.org/api/records/{ZENODO_ID}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        # Find the first file in the 'files' list
        files = data.get('files', [])
        if not files:
            logger.error(f"No files found in Zenodo record {ZENODO_ID}")
            return False
        
        # Assume the first file is our dataset (or the only one)
        file_info = files[0]
        filename = file_info.get('key')
        download_url = f"https://zenodo.org/record/{ZENODO_ID}/files/{filename}"
        
        # Checksum from Zenodo metadata
        expected_checksum = file_info.get('checksum', '').replace('sha256:', '')
        
        logger.info(f"Found file: {filename}")
        logger.info(f"Expected checksum: {expected_checksum}")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch Zenodo metadata: {e}")
        return False

    # Define paths
    DATA_RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    temp_dir = Path(tempfile.mkdtemp())
    tarball_path = temp_dir / filename
    output_csv_path = DATA_RAW_DIR / "barrier_dataset.csv"

    # Step 1: Download
    if not download_file(download_url, tarball_path, logger):
        return False

    # Step 2: Verify Checksum
    if not verify_checksum(tarball_path, expected_checksum, logger):
        return False

    # Step 3: Extract/Convert to CSV
    if not convert_to_csv(tarball_path, output_csv_path, logger):
        return False

    # Step 4: Final Verification
    if not output_csv_path.exists():
        logger.error(f"Output file {output_csv_path} does not exist after processing.")
        return False

    logger.info(f"Data fetch and verification successful. File: {output_csv_path}")
    return True

def main():
    logger = setup_logger()
    logger.info("Starting data fetch and verification process.")
    
    success = fetch_and_verify_data(logger)
    
    if not success:
        logger.error("Data fetch and verification failed.")
        sys.exit(1)
    else:
        logger.info("Data fetch and verification completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
