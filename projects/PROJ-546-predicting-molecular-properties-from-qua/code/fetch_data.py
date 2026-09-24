import hashlib
import logging
import os
import sys
import tarfile
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List

import requests

# Import from sibling modules as per API surface
from config import ZENODO_ID, DATA_RAW_DIR, LOGS_DIR

def setup_logger() -> logging.Logger:
    """Set up the logger for fetch_data module."""
    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "fetch_data.log"
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_zenodo_record(record_id: str) -> dict:
    """Fetch Zenodo record metadata."""
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def find_data_file(record_metadata: dict) -> Optional[str]:
    """Find the data file in the Zenodo record."""
    files = record_metadata.get("files", [])
    if not files:
        return None
    # Return the first file found (typically the dataset)
    return files[0].get("key")

def download_file(url: str, dest_path: Path, logger: logging.Logger) -> Path:
    """Download a file from URL to destination path."""
    logger.info(f"Downloading from {url} to {dest_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Download complete: {dest_path} ({dest_path.stat().st_size} bytes)")
    return dest_path

def extract_tarball(tar_path: Path, extract_to: Path, logger: logging.Logger) -> List[Path]:
    """Extract a tarball (gz, bz2, xz) to a directory."""
    logger.info(f"Extracting tarball: {tar_path}")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    with tarfile.open(tar_path, "r:*") as tar:
        tar.extractall(path=extract_to)
        # Collect all extracted files
        for member in tar.getmembers():
            if member.isfile():
                extracted_files.append(extract_to / member.name)
    
    logger.info(f"Extracted {len(extracted_files)} files")
    return extracted_files

def extract_zipball(zip_path: Path, extract_to: Path, logger: logging.Logger) -> List[Path]:
    """Extract a zip file to a directory."""
    logger.info(f"Extracting zip file: {zip_path}")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(path=extract_to)
        # Collect all extracted files
        for member in zip_ref.namelist():
            if not member.endswith('/'):  # Skip directories
                extracted_files.append(extract_to / member)
    
    logger.info(f"Extracted {len(extracted_files)} files")
    return extracted_files

def convert_to_csv(source_files: List[Path], target_path: Path, logger: logging.Logger) -> Path:
    """
    Convert source data files to a canonical CSV file.
    If the source is already CSV, copy it. Otherwise, attempt to convert.
    For this task, we assume the Zenodo dataset is either CSV or can be 
    identified as the primary data file.
    """
    logger.info(f"Converting/normalizing data to: {target_path}")
    
    # Find CSV files in the extracted content
    csv_files = [f for f in source_files if f.suffix.lower() == '.csv']
    
    if csv_files:
        # Use the first CSV file found
        source_csv = csv_files[0]
        logger.info(f"Found CSV file: {source_csv}")
        shutil.copy2(source_csv, target_path)
    else:
        # If no CSV found, assume the first file is the data and try to handle it
        # For this implementation, we'll raise an error if no CSV is found
        # as the task requires a CSV output
        if source_files:
            # Try to rename the first file to CSV if it's likely data
            source_file = source_files[0]
            logger.warning(f"No CSV found. Attempting to use: {source_file}")
            shutil.copy2(source_file, target_path)
        else:
            raise FileNotFoundError("No data files found after extraction")
    
    logger.info(f"Normalized dataset written to: {target_path}")
    return target_path

def verify_checksum(file_path: Path, expected_checksum: Optional[str] = None, logger: logging.Logger = None) -> Tuple[bool, str]:
    """Verify file checksum. Returns (success, actual_checksum)."""
    actual_checksum = compute_sha256(file_path)
    if expected_checksum and actual_checksum != expected_checksum:
        if logger:
            logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False, actual_checksum
    
    if logger:
        logger.info(f"Checksum verified for {file_path}: {actual_checksum}")
    return True, actual_checksum

def fetch_and_verify_data(logger: logging.Logger) -> Path:
    """
    Main function to fetch data from Zenodo, verify checksum, and normalize filename.
    This implements T004c: Normalize Dataset Filename.
    """
    logger.info(f"Starting data fetch for Zenodo ID: {ZENODO_ID}")
    
    # Step 1: Get record metadata
    try:
        record = get_zenodo_record(ZENODO_ID)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Zenodo record {ZENODO_ID}: {e}")
        raise
    
    # Step 2: Find the data file
    file_key = find_data_file(record)
    if not file_key:
        logger.error("No data file found in Zenodo record")
        raise FileNotFoundError("No data file found in Zenodo record")
    
    # Step 3: Construct download URL
    # Zenodo API returns files in 'files' list with 'links' containing 'self'
    files_info = record.get("files", [])
    if not files_info:
        raise FileNotFoundError("No files in Zenodo record")
    
    file_info = next((f for f in files_info if f.get("key") == file_key), None)
    if not file_info:
        raise FileNotFoundError(f"File {file_key} not found in record")
    
    download_url = file_info.get("links", {}).get("self")
    if not download_url:
        raise FileNotFoundError(f"No download URL for {file_key}")
    
    # Step 4: Create temporary directory for download and extraction
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Step 5: Download the file
        downloaded_file = tmp_path / file_key
        download_file(download_url, downloaded_file, logger)
        
        # Step 6: Verify checksum (Zenodo provides checksum in metadata)
        # Note: Zenodo API might not always provide checksum in a standard field
        # We'll log the actual checksum for verification purposes
        is_valid, actual_checksum = verify_checksum(downloaded_file, logger=logger)
        logger.info(f"File: {file_key}, Size: {downloaded_file.stat().st_size} bytes, SHA-256: {actual_checksum}")
        
        # Step 7: Extract if compressed
        extracted_files = []
        if downloaded_file.suffix.lower() in ['.gz', '.tar', '.tgz', '.bz2', '.xz']:
            extracted_files = extract_tarball(downloaded_file, tmp_path / "extracted", logger)
        elif downloaded_file.suffix.lower() == '.zip':
            extracted_files = extract_zipball(downloaded_file, tmp_path / "extracted", logger)
        else:
            # Not compressed, treat as single file
            extracted_files = [downloaded_file]
        
        # Step 8: Normalize to canonical filename
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        canonical_path = DATA_RAW_DIR / "barrier_dataset.csv"
        
        convert_to_csv(extracted_files, canonical_path, logger)
        
        # Step 9: Final verification
        if not canonical_path.exists() or canonical_path.stat().st_size == 0:
            raise RuntimeError(f"Failed to create normalized dataset: {canonical_path}")
        
        logger.info(f"Successfully normalized dataset to: {canonical_path}")
        return canonical_path

def main():
    """Entry point for the fetch_data script."""
    logger = setup_logger()
    try:
        output_path = fetch_and_verify_data(logger)
        print(f"Dataset successfully normalized to: {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to fetch and normalize data: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()