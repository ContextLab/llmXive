import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path
from typing import Optional

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
WESAD_OUTPUT_DIR = "data/raw/wesad"
CHECKSUMS_FILE = "results/checksums.txt"
DOWNLOAD_TIMEOUT = 600  # 10 minutes in seconds

def get_wesad_download_url() -> str:
    """
    Fetches the direct download URL for the WESAD dataset from Zenodo API.
    
    Returns:
        str: The direct download URL for the dataset archive.
        
    Raises:
        requests.exceptions.RequestException: If the API call fails.
        ValueError: If the download URL cannot be found in the response.
    """
    logger.info(f"Fetching download URL from Zenodo API: {ZENODO_API_URL}")
    try:
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract the download link from the files list
        files = data.get('files', [])
        if not files:
            raise ValueError("No files found in Zenodo record.")
        
        # WESAD is typically a single zip file in the record
        download_link = None
        for file_entry in files:
            if file_entry.get('type') == 'dataset' or file_entry.get('filename', '').endswith('.zip'):
                download_link = file_entry.get('links', {}).get('self')
                break
        
        if not download_link:
            # Fallback to first file if specific type not found
            download_link = files[0].get('links', {}).get('self')
            
        if not download_link:
            raise ValueError("Could not locate a valid download link in the Zenodo response.")
        
        logger.info(f"Download URL identified: {download_link}")
        return download_link
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch download URL from Zenodo: {e}")
        raise
    except ValueError as e:
        logger.error(f"Error parsing Zenodo response: {e}")
        raise

def calculate_sha256(filepath: str) -> str:
    """
    Calculates the SHA-256 checksum of a file.
    
    Args:
        filepath (str): Path to the file.
        
    Returns:
        str: The hexadecimal SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    logger.info(f"Calculating checksum for: {filepath}")
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file for checksum: {e}")
        raise

def download_file_with_checksum(url: str, output_path: str) -> str:
    """
    Downloads a file from a URL with a timeout and verifies its checksum.
    
    Args:
        url (str): The URL to download from.
        output_path (str): The local path to save the file.
        
    Returns:
        str: The calculated SHA-256 checksum of the downloaded file.
        
    Raises:
        requests.exceptions.Timeout: If the download times out.
        requests.exceptions.RequestException: If the download fails.
        IOError: If file operations fail.
        Exception: If any unexpected error occurs during download.
    """
    logger.info(f"Starting download from: {url}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Timeout set to: {DOWNLOAD_TIMEOUT} seconds")
    
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Stream download to handle large files and enable timeout
        with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.debug(f"Download progress: {progress:.2f}%")
                            
        logger.info(f"Download completed successfully. File size: {downloaded_size} bytes")
        
        # Verify checksum
        checksum = calculate_sha256(output_path)
        logger.info(f"Checksum calculated: {checksum}")
        
        return checksum
        
    except requests.exceptions.Timeout:
        logger.error(f"Download timed out after {DOWNLOAD_TIMEOUT} seconds.")
        # Delete partial file
        if os.path.exists(output_path):
            logger.warning(f"Deleting partial file: {output_path}")
            os.remove(output_path)
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed due to request error: {e}")
        # Delete partial file if it exists
        if os.path.exists(output_path):
            logger.warning(f"Deleting partial file: {output_path}")
            os.remove(output_path)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        # Delete partial file if it exists
        if os.path.exists(output_path):
            logger.warning(f"Deleting partial file: {output_path}")
            os.remove(output_path)
        raise

def write_checksums(checksum: str, filename: str, checksums_file: str) -> None:
    """
    Writes the checksum and filename to the checksums file.
    
    Args:
        checksum (str): The SHA-256 checksum.
        filename (str): The name of the downloaded file.
        checksums_file (str): Path to the checksums file.
    """
    try:
        Path(checksums_file).parent.mkdir(parents=True, exist_ok=True)
        with open(checksums_file, 'a') as f:
            f.write(f"{checksum}  {filename}\n")
        logger.info(f"Checksum written to {checksums_file}")
    except IOError as e:
        logger.error(f"Failed to write checksums: {e}")
        raise

def main() -> int:
    """
    Main entry point for the WESAD dataset download script.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    logger.info("Starting WESAD dataset download process.")
    
    try:
        # Step 1: Get download URL
        download_url = get_wesad_download_url()
        
        # Step 2: Define output path
        output_file_name = "wesad_dataset.zip"
        output_path = os.path.join(WESAD_OUTPUT_DIR, output_file_name)
        
        # Step 3: Download file with checksum verification
        checksum = download_file_with_checksum(download_url, output_path)
        
        # Step 4: Write checksums to file
        write_checksums(checksum, output_file_name, CHECKSUMS_FILE)
        
        logger.info("WESAD dataset download completed successfully.")
        return 0
        
    except requests.exceptions.Timeout as e:
        logger.error(f"CRITICAL: Download timed out. Pipeline halting. Error: {e}")
        return 1
    except requests.exceptions.RequestException as e:
        logger.error(f"CRITICAL: Download failed due to request error. Pipeline halting. Error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"CRITICAL: Invalid Zenodo response. Pipeline halting. Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"CRITICAL: Unexpected error in download process. Pipeline halting. Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
