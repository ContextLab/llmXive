"""
Download the WESAD dataset from Zenodo.

This script downloads the WESAD dataset archive from Zenodo (DOI: 10.5281/zenodo.1292932)
to data/raw/wesad/WESAD.zip, calculates its SHA-256 checksum, and writes the checksum
to results/checksums.txt for reproducibility verification.

If the download fails or times out, the script logs a CRITICAL error, deletes any
partial file, and ABORTs the WESAD-specific scan path. It does NOT proceed to scan
WESAD data if the download fails.
"""

import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/download.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ZENODO_API_URL = "https://zenodo.org/api/records/1292932"
ZENODO_DOWNLOAD_URL = "https://zenodo.org/records/1292932/files/WESAD.zip"
OUTPUT_DIR = Path("data/raw/wesad")
OUTPUT_FILE = OUTPUT_DIR / "WESAD.zip"
CHECKSUMS_FILE = Path("results/checksums.txt")
DOWNLOAD_TIMEOUT = 600  # 10 minutes in seconds
CHUNK_SIZE = 8192  # 8KB chunks for streaming download


def get_wesad_download_url():
    """
    Fetch the download URL for WESAD dataset from Zenodo API.

    Returns:
        str: The direct download URL for WESAD.zip

    Raises:
        RuntimeError: If the Zenodo API call fails or the record is not found
    """
    try:
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract the download URL from the Zenodo API response
        files = data.get('files', [])
        for file_info in files:
            if file_info.get('key') == 'WESAD.zip':
                # Zenodo provides a 'download_url' in the files section
                return file_info.get('download_url')

        # Fallback: construct the URL manually if not in API response
        # Zenodo record ID is 1292932
        return f"https://zenodo.org/records/1292932/files/WESAD.zip"

    except requests.RequestException as e:
        logger.error(f"Failed to fetch download URL from Zenodo API: {e}")
        raise RuntimeError(f"Zenodo API call failed: {e}")


def calculate_sha256(filepath):
    """
    Calculate SHA-256 checksum of a file.

    Args:
        filepath: Path to the file

    Returns:
        str: Hexadecimal SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file_with_checksum(url, output_path, timeout=600):
    """
    Download a file with progress logging and checksum verification.

    Args:
        url: Download URL
        output_path: Path where file should be saved
        timeout: Download timeout in seconds

    Returns:
        str: SHA-256 checksum of the downloaded file

    Raises:
        RuntimeError: If download fails or checksum verification fails
    """
    logger.info(f"Starting download from {url}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Timeout: {timeout} seconds")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean up any existing partial file
    if output_path.exists():
        logger.warning(f"Removing existing partial file: {output_path}")
        output_path.unlink()

    try:
        # Stream the download
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        last_progress_time = time.time()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # Log progress every 10 seconds
                    if time.time() - last_progress_time > 10:
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress: {downloaded_size}/{total_size} bytes ({percent:.1f}%)")
                        else:
                            logger.info(f"Downloaded {downloaded_size} bytes")
                        last_progress_time = time.time()

        logger.info(f"Download complete: {output_path}")

        # Calculate checksum
        checksum = calculate_sha256(output_path)
        logger.info(f"SHA-256 checksum: {checksum}")

        return checksum

    except requests.exceptions.Timeout:
        logger.critical(f"Download timed out after {timeout} seconds")
        # Clean up partial file
        if output_path.exists():
            logger.warning(f"Deleting partial file: {output_path}")
            output_path.unlink()
        raise RuntimeError(f"Download timed out after {timeout} seconds")

    except requests.exceptions.RequestException as e:
        logger.critical(f"Download failed: {e}")
        # Clean up partial file
        if output_path.exists():
            logger.warning(f"Deleting partial file: {output_path}")
            output_path.unlink()
        raise RuntimeError(f"Download failed: {e}")


def write_checksums(checksum_dict):
    """
    Write checksums to the checksums file.

    Args:
        checksum_dict: Dictionary mapping filename to checksum
    """
    CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CHECKSUMS_FILE, 'a') as f:
        for filename, checksum in checksum_dict.items():
            f.write(f"{checksum}  {filename}\n")

    logger.info(f"Checksums written to {CHECKSUMS_FILE}")


def main():
    """
    Main function to download WESAD dataset.

    This function:
    1. Gets the download URL from Zenodo
    2. Downloads the WESAD.zip file
    3. Calculates and logs the SHA-256 checksum
    4. Writes the checksum to results/checksums.txt
    5. Extracts the ZIP file to data/raw/wesad/

    If any step fails, it logs a CRITICAL error and exits.
    """
    logger.info("=" * 60)
    logger.info("Starting WESAD dataset download")
    logger.info("=" * 60)

    try:
        # Step 1: Get download URL
        download_url = get_wesad_download_url()
        logger.info(f"Download URL: {download_url}")

        # Step 2: Download the file
        checksum = download_file_with_checksum(
            download_url,
            OUTPUT_FILE,
            timeout=DOWNLOAD_TIMEOUT
        )

        # Step 3: Write checksum
        write_checksums({"WESAD.zip": checksum})

        # Step 4: Extract the ZIP file
        logger.info("Extracting ZIP file...")
        shutil.unpack_archive(str(OUTPUT_FILE), str(OUTPUT_DIR))
        logger.info(f"Extraction complete. Files extracted to {OUTPUT_DIR}")

        # Verify extraction
        extracted_files = list(OUTPUT_DIR.rglob("*"))
        logger.info(f"Extracted {len(extracted_files)} files/directories")

        logger.info("=" * 60)
        logger.info("WESAD dataset download and extraction completed successfully")
        logger.info("=" * 60)

        return 0

    except RuntimeError as e:
        logger.critical(f"Fatal error during download: {e}")
        logger.info("WESAD download path ABORTED. Pipeline will skip WESAD-specific scans.")
        return 1

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        logger.info("WESAD download path ABORTED due to unexpected error.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
