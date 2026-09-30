import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path

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
WESAD_ZENODO_DOI = "10.5281/zenodo.1292932"
# Zenodo API endpoint for latest version of a record
ZENODO_API_URL = f"https://zenodo.org/api/records/{WESAD_ZENODO_DOI.split('.')[-1]}"
WESAD_FILENAME = "WESAD.zip"
WESAD_OUTPUT_DIR = Path("data/raw/wesad")
CHECKSUMS_FILE = Path("results/checksums.txt")
DOWNLOAD_TIMEOUT = 600  # 10 minutes in seconds

def get_wesad_download_url():
    """
    Fetches the download URL for the WESAD dataset from Zenodo API.
    Returns the direct download link for the archive file.
    """
    try:
        logger.info(f"Fetching download URL from Zenodo for DOI: {WESAD_ZENODO_DOI}")
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Find the file with the correct name
        files = data.get('files', [])
        download_url = None
        for file_info in files:
            if file_info.get('key') == WESAD_FILENAME:
                download_url = file_info.get('links', {}).get('self')
                break
        
        if not download_url:
            logger.error(f"Could not find '{WESAD_FILENAME}' in Zenodo record files.")
            return None
        
        logger.info(f"Found download URL: {download_url}")
        return download_url
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Zenodo record: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Zenodo record: {e}")
        return None

def calculate_sha256(file_path):
    """
    Calculates the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        return None

def download_file_with_checksum(url, output_path, timeout):
    """
    Downloads a file from the given URL to the output path with a timeout.
    Returns the SHA-256 checksum of the downloaded file if successful, None otherwise.
    """
    try:
        logger.info(f"Starting download from {url} to {output_path}")
        start_time = time.time()
        
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        logger.info(f"Download progress: {progress:.2f}%")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Download completed in {elapsed_time:.2f} seconds.")
        
        checksum = calculate_sha256(output_path)
        if checksum:
            logger.info(f"SHA-256 checksum: {checksum}")
            return checksum
        else:
            logger.error("Failed to calculate checksum.")
            return None
    
    except requests.exceptions.Timeout:
        logger.error(f"Download timed out after {timeout} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return None

def write_checksums(checksum, filename):
    """
    Writes the checksum and filename to the checksums file.
    """
    try:
        with open(CHECKSUMS_FILE, 'a') as f:
            f.write(f"{checksum}  {filename}\n")
        logger.info(f"Checksum written to {CHECKSUMS_FILE}")
    except Exception as e:
        logger.error(f"Failed to write checksum to {CHECKSUMS_FILE}: {e}")

def main():
    """
    Main function to download the WESAD dataset.
    """
    logger.info("Starting T010: Download WESAD dataset")
    
    # Ensure output directory exists
    WESAD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = WESAD_OUTPUT_DIR / WESAD_FILENAME
    
    # Remove partial file if it exists
    if output_path.exists():
        logger.warning(f"Partial file {output_path} exists. Deleting it.")
        try:
            output_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete partial file {output_path}: {e}")
            # Continue anyway, as per task requirements
    
    # Get download URL
    download_url = get_wesad_download_url()
    if not download_url:
        logger.error("Failed to get download URL. Cannot proceed.")
        return 1
    
    # Download file
    checksum = download_file_with_checksum(download_url, output_path, DOWNLOAD_TIMEOUT)
    
    if checksum:
        logger.info("Download successful.")
        write_checksums(checksum, WESAD_FILENAME)
        logger.info("T010 completed successfully.")
        return 0
    else:
        logger.error("Download failed or timed out. Deleting partial file.")
        if output_path.exists():
            try:
                output_path.unlink()
                logger.info(f"Deleted partial file {output_path}")
            except Exception as e:
                logger.error(f"Failed to delete partial file {output_path}: {e}")
        # Do not exit with error code; pipeline continues to T011a
        logger.info("T010 failed, but pipeline will continue to T011a.")
        return 0

if __name__ == "__main__":
    sys.exit(main())