"""
Fetch the Pantheon+ dataset from Zenodo and verify its checksum.

This script downloads the Pantheon+ Supernova dataset from the specified Zenodo
repository (Record ID: 10.5281/zenodo.1002345), saves it to the raw data directory,
and verifies the file integrity using the checksum utility from T009.

The script is designed to run as:
    python code/scripts/fetch_pantheon_plus.py

It relies on the configuration and data integrity utilities defined in:
    - src.utils.config for project paths
    - src.utils.data_integrity for checksum verification
    - src.utils.logger for logging
"""

import os
import sys
import logging
import hashlib
import shutil
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Add the project root to the path to allow relative imports
# Assuming this script is run from the project root or code/scripts
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_project_paths, ensure_directories_exist
from src.utils.data_integrity import compute_checksum, verify_checksum
from src.utils.logger import get_logger, setup_logging

# Constants
ZENODO_RECORD_ID = "10.5281/zenodo.1002345"
# The specific file name within the Zenodo record.
# Pantheon+ is typically distributed as a CSV. We assume the main data file.
# If the record contains multiple files, this URL would need adjustment to the specific file ID.
# Based on standard Pantheon+ releases, the file is often named 'pantheon_plus.csv' or similar.
# We will construct the direct download URL if possible, or use the Zenodo API to find the file.
# For robustness, we assume the file name matches the expected output.
EXPECTED_FILENAME = "pantheon_plus.csv"

# Checksum configuration (SHA-256)
# In a real scenario, this checksum would be provided by the data provider (Zenodo record metadata).
# Since the task description implies we verify against a known checksum, we define a placeholder.
# If the task implies fetching a known checksum from the record, we would parse the Zenodo API.
# For this implementation, we assume the checksum is provided in the environment or config.
# If not provided, we will download and compute the checksum, then save it for future verification.
EXPECTED_CHECKSUM_ENV = "PANETHEON_PLUS_CHECKSUM"

def get_download_url(record_id: str, filename: str) -> str:
    """
    Constructs the direct download URL for a file in a Zenodo record.
    
    Zenodo API: https://zenodo.org/api/records/{record_id}
    We fetch the metadata to find the correct file ID.
    """
    import json
    import urllib.request
    
    api_url = f"https://zenodo.org/api/records/{record_id}"
    
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to fetch Zenodo metadata for record {record_id}: {e}")

    files = data.get('files', [])
    if not files:
        # Try to find files in the 'metadata' -> 'files' if the structure is different
        # Some Zenodo records structure files differently.
        # Let's look for the specific filename.
        pass

    target_file = None
    for f in files:
        if f.get('filename') == filename:
            target_file = f
            break
    
    if not target_file:
        # Fallback: If the record ID is a DOI, sometimes the file is directly accessible
        # or the record contains a single file.
        # If the record ID is actually a DOI, we might need to resolve it.
        # However, 10.5281/zenodo.1002345 is a valid Zenodo ID format.
        # If the file list is empty, we might be looking at a different record structure.
        # Let's assume the first file if only one exists, or raise error if multiple and not found.
        if len(files) == 1:
            target_file = files[0]
        else:
            available_names = [f.get('filename', 'unknown') for f in files]
            raise FileNotFoundError(
                f"File '{filename}' not found in Zenodo record {record_id}. "
                f"Available files: {available_names}"
            )

    # The download link is usually in 'links' -> 'self' or 'download'
    download_link = target_file.get('links', {}).get('download')
    if not download_link:
        # Fallback to 'self' if download is missing
        download_link = target_file.get('links', {}).get('self')
    
    if not download_link:
        raise RuntimeError(f"Could not find download link for file '{filename}' in record {record_id}")

    return download_link

def download_file(url: str, destination: Path, logger: logging.Logger):
    """Downloads a file from a URL to a destination path."""
    logger.info(f"Downloading from {url} to {destination}")
    try:
        # Use a temporary file to ensure atomicity and avoid partial downloads
        temp_path = destination.with_suffix(destination.suffix + '.tmp')
        urlretrieve(url, str(temp_path))
        
        # Move temp file to final destination
        shutil.move(str(temp_path), str(destination))
        logger.info(f"Download complete: {destination}")
    except (URLError, HTTPError, OSError) as e:
        raise RuntimeError(f"Failed to download file from {url}: {e}")

def main():
    """Main entry point for the fetch script."""
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)

    # Get project paths
    try:
        paths = get_project_paths()
    except Exception as e:
        logger.error(f"Failed to get project paths: {e}")
        sys.exit(1)

    raw_data_dir = paths.get('raw', paths['data'] / 'raw')
    ensure_directories_exist([raw_data_dir])

    output_file = raw_data_dir / EXPECTED_FILENAME
    logger.info(f"Target output file: {output_file}")

    # Check if file already exists to avoid re-downloading
    if output_file.exists():
        logger.info(f"File {output_file} already exists. Verifying checksum...")
    else:
        # Get download URL
        try:
            download_url = get_download_url(ZENODO_RECORD_ID, EXPECTED_FILENAME)
        except Exception as e:
            logger.error(f"Failed to retrieve download URL: {e}")
            sys.exit(1)

        # Download the file
        try:
            download_file(download_url, output_file, logger)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            sys.exit(1)

    # Verify checksum
    # We need the expected checksum. If not in env, we cannot verify strictly.
    # However, the task requires verification.
    # If the environment variable is not set, we compute the checksum and log it,
    # but we cannot "verify" against a known good value unless we have it.
    # For the purpose of this task, we assume the environment variable is set
    # or we treat the first run as establishing the baseline if the env var is missing.
    # BUT the constraint says: "verify checksum against data/raw/pantheon_plus.csv using T009".
    # T009 (data_integrity) has verify_checksum which takes expected and actual.
    # If we don't have the expected value, we can't verify.
    
    expected_checksum = os.environ.get(EXPECTED_CHECKSUM_ENV)
    
    if not expected_checksum:
        logger.warning(f"Environment variable {EXPECTED_CHECKSUM_ENV} not set. "
                       f"Cannot verify checksum against a known value. "
                       f"Computing checksum for reference: {compute_checksum(output_file)}")
        # We proceed but note the lack of verification.
        # In a strict pipeline, this might be a failure.
        # However, the task says "verify checksum... using T009".
        # If we can't verify, we might fail loudly.
        # Let's assume for this implementation that if the checksum is not provided,
        # we skip the strict verification but log the computed one.
        # If the task implies the checksum is known, we must have it.
        # Since we can't fabricate, we will let the run proceed but warn.
        # If the user expects a hard fail, they should set the env var.
        # Re-reading constraint: "verify checksum ... using T009".
        # If we can't, we should probably fail or skip.
        # Let's assume the environment variable is expected to be set by the pipeline.
        # If not, we fail loudly to adhere to "fail loudly, never silently".
        logger.error(f"Verification failed: Expected checksum not provided in environment variable {EXPECTED_CHECKSUM_ENV}.")
        sys.exit(1)

    computed_checksum = compute_checksum(output_file)
    
    logger.info(f"Computed checksum: {computed_checksum}")
    logger.info(f"Expected checksum: {expected_checksum}")

    if not verify_checksum(computed_checksum, expected_checksum):
        logger.error(f"Checksum verification FAILED! File may be corrupted.")
        sys.exit(1)

    logger.info(f"Checksum verification PASSED. File integrity confirmed.")
    logger.info(f"Task T014 completed successfully: {output_file}")

if __name__ == "__main__":
    main()
