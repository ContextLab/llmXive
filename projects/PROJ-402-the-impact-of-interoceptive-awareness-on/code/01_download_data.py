"""
Download WESAD dataset from Zenodo.

This script downloads the WESAD dataset archive from Zenodo (DOI: 10.5281/zenodo.1292932)
to data/raw/wesad/. It enforces strict error handling: if the download fails or times out,
it deletes any partial file, logs the error, and exits with a non-zero code.

No fallback to synthetic data is implemented.
"""
import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ZENODO_API_URL = "https://zenodo.org/api/records/1292932"
WESAD_ARCHIVE_NAME = "WESAD.zip"
OUTPUT_DIR = Path("data/raw/wesad")
TIMEOUT_SECONDS = 600  # 10 minutes
CHUNK_SIZE = 8192

def get_wesad_download_url() -> str:
    """
    Fetch the download URL for the WESAD dataset from Zenodo API.
    
    Returns:
        str: Direct download URL for the WESAD archive.
    
    Raises:
        requests.exceptions.RequestException: If the API call fails.
        ValueError: If the download URL cannot be found in the response.
    """
    try:
        logger.info(f"Fetching download URL from Zenodo API: {ZENODO_API_URL}")
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Navigate to the files section
        files = data.get('files', [])
        if not files:
            raise ValueError("No files found in Zenodo response")
        
        # Find the main archive (usually the largest file or named WESAD.zip)
        download_url = None
        for file_info in files:
            if file_info.get('key') == WESAD_ARCHIVE_NAME or 'WESAD' in file_info.get('key', ''):
                download_url = file_info.get('links', {}).get('self')
                break
        
        if not download_url:
            # Fallback: use the first file if specific name not found
            logger.warning(f"Could not find {WESAD_ARCHIVE_NAME} by name, using first available file")
            download_url = files[0].get('links', {}).get('self')
        
        if not download_url:
            raise ValueError("No valid download URL found in Zenodo response")
        
        logger.info(f"Found download URL: {download_url}")
        return download_url
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch download URL from Zenodo: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse Zenodo response: {e}")
        raise

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        str: Hexadecimal SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_file_with_checksum(url: str, output_path: Path) -> Tuple[str, str]:
    """
    Download a file with progress logging and calculate its checksum.
    
    Args:
        url: Download URL.
        output_path: Path to save the downloaded file.
    
    Returns:
        Tuple of (file_path, checksum).
    
    Raises:
        requests.exceptions.Timeout: If download times out.
        requests.exceptions.RequestException: If download fails.
    """
    logger.info(f"Starting download from: {url}")
    logger.info(f"Output path: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        last_log_time = time.time()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Log progress every 10 seconds or on completion
                    current_time = time.time()
                    if current_time - last_log_time > 10 or downloaded_size == total_size:
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress: {downloaded_size / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)")
                        else:
                            logger.info(f"Downloaded: {downloaded_size / (1024*1024):.1f} MB")
                        last_log_time = current_time
        
        logger.info("Download completed successfully")
        
        # Calculate checksum
        checksum = calculate_sha256(output_path)
        logger.info(f"SHA-256 checksum: {checksum}")
        
        return str(output_path), checksum
        
    except requests.exceptions.Timeout:
        logger.error(f"Download timed out after {TIMEOUT_SECONDS} seconds")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise

def write_checksums(checksums: list, output_path: Path):
    """
    Write checksums to a file.
    
    Args:
        checksums: List of (filename, checksum) tuples.
        output_path: Path to the checksums file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for filename, checksum in checksums:
            f.write(f"{checksum}  {filename}\n")
    logger.info(f"Checksums written to {output_path}")

def main():
    """
    Main function to download WESAD dataset.
    
    Returns:
        int: 0 on success, non-zero on failure.
    """
    logger.info("=" * 60)
    logger.info("Starting WESAD dataset download")
    logger.info("=" * 60)
    
    try:
        # Get download URL
        download_url = get_wesad_download_url()
        
        # Define output path
        output_file = OUTPUT_DIR / WESAD_ARCHIVE_NAME
        
        # Download file
        file_path, checksum = download_file_with_checksum(download_url, output_file)
        
        # Write checksums
        checksums_file = Path("results/checksums.txt")
        write_checksums([(WESAD_ARCHIVE_NAME, checksum)], checksums_file)
        
        logger.info("=" * 60)
        logger.info("WESAD dataset download completed successfully")
        logger.info(f"File: {file_path}")
        logger.info(f"Checksum: {checksum}")
        logger.info("=" * 60)
        
        return 0
        
    except requests.exceptions.Timeout as e:
        logger.error(f"TIMEOUT: Download timed out after {TIMEOUT_SECONDS} seconds")
        logger.error(f"Error details: {e}")
        
        # Delete partial file if it exists
        if OUTPUT_DIR.exists() and (OUTPUT_DIR / WESAD_ARCHIVE_NAME).exists():
            logger.warning(f"Deleting partial file: {OUTPUT_DIR / WESAD_ARCHIVE_NAME}")
            try:
                (OUTPUT_DIR / WESAD_ARCHIVE_NAME).unlink()
                logger.info("Partial file deleted successfully")
            except Exception as delete_error:
                logger.error(f"Failed to delete partial file: {delete_error}")
        
        logger.error("Exiting with non-zero code due to timeout")
        return 1
        
    except requests.exceptions.RequestException as e:
        logger.error(f"NETWORK ERROR: Download failed due to network error")
        logger.error(f"Error details: {e}")
        
        # Delete partial file if it exists
        if OUTPUT_DIR.exists() and (OUTPUT_DIR / WESAD_ARCHIVE_NAME).exists():
            logger.warning(f"Deleting partial file: {OUTPUT_DIR / WESAD_ARCHIVE_NAME}")
            try:
                (OUTPUT_DIR / WESAD_ARCHIVE_NAME).unlink()
                logger.info("Partial file deleted successfully")
            except Exception as delete_error:
                logger.error(f"Failed to delete partial file: {delete_error}")
        
        logger.error("Exiting with non-zero code due to network error")
        return 1
        
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {e}")
        logger.error("Exiting with non-zero code")
        return 1

if __name__ == "__main__":
    sys.exit(main())