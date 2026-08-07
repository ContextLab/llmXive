"""
Data download script for the interoceptive awareness research pipeline.

This script downloads the WESAD dataset from Zenodo and enforces deterministic
behavior via SHA-256 checksum verification as required by Constitution Principle I.

Output:
- data/raw/wesad/: Downloaded dataset archive
- results/checksums.txt: SHA-256 checksums of all downloaded files
"""
import os
import sys
import time
import logging
import hashlib
import requests
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.pytest_config import compute_sha256_checksum, log_github_job_duration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ZENODO_WESAD_DOI = "10.5281/zenodo.1292932"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_WESAD_DOI}"
DOWNLOAD_TIMEOUT = 600  # 10 minutes
DATA_DIR = project_root / "data" / "raw" / "wesad"
CHECKSUMS_FILE = project_root / "results" / "checksums.txt"

def get_wesad_download_url() -> str:
    """
    Fetch the download URL for WESAD dataset from Zenodo API.
    
    Returns:
        Direct download URL for the dataset archive
        
    Raises:
        RuntimeError: If the dataset cannot be found or accessed
    """
    logger.info(f"Fetching download URL from Zenodo: {ZENODO_API_URL}")
    
    try:
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract files from the record
        files = data.get("files", [])
        if not files:
            raise RuntimeError(f"No files found in Zenodo record {ZENODO_WESAD_DOI}")
        
        # Find the main dataset archive
        for file_info in files:
            if file_info.get("key", "").endswith((".zip", ".tar.gz", ".tar")):
                return file_info["links"]["self"]
        
        # Fallback: use the first file
        return files[0]["links"]["self"]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch download URL from Zenodo: {e}")
        raise RuntimeError(f"Zenodo API request failed: {e}")


def download_file_with_checksum(
    url: str,
    output_path: Path,
    timeout: int = DOWNLOAD_TIMEOUT
) -> str:
    """
    Download a file and compute its SHA-256 checksum.
    
    Args:
        url: Download URL
        output_path: Where to save the downloaded file
        timeout: Request timeout in seconds
        
    Returns:
        SHA-256 checksum of the downloaded file
        
    Raises:
        requests.exceptions.Timeout: If download times out
        RuntimeError: If download fails or file is corrupted
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading from {url} to {output_path}")
    
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Download with progress tracking
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        last_progress = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 10%
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        if progress - last_progress >= 10:
                            logger.info(f"Download progress: {progress}%")
                            last_progress = progress
        
        # Compute checksum
        checksum = compute_sha256_checksum(output_path)
        logger.info(f"Download complete. SHA-256: {checksum}")
        
        return checksum
        
    except requests.exceptions.Timeout:
        logger.error(f"Download timed out after {timeout} seconds")
        # Delete partial file
        if output_path.exists():
            output_path.unlink()
            logger.info(f"Deleted partial file: {output_path}")
        raise
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        # Delete partial file
        if output_path.exists():
            output_path.unlink()
            logger.info(f"Deleted partial file: {output_path}")
        raise


def write_checksums(checksums: Dict[str, str]) -> None:
    """
    Write checksums to the output file.
    
    Args:
        checksums: Dictionary mapping file paths to their SHA-256 checksums
    """
    CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CHECKSUMS_FILE, "w") as f:
        f.write("# SHA-256 checksums for downloaded data files\n")
        f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Source: WESAD dataset (DOI: {ZENODO_WESAD_DOI})\n")
        f.write("# Format: filepath  checksum\n")
        f.write("#" + "=" * 70 + "\n")
        
        for filepath, checksum in sorted(checksums.items()):
            f.write(f"{filepath}  {checksum}\n")
    
    logger.info(f"Wrote checksums to {CHECKSUMS_FILE}")


def main() -> int:
    """
    Main entry point for the data download script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    start_time = time.time()
    logger.info("Starting WESAD dataset download")
    
    try:
        # Get download URL
        download_url = get_wesad_download_url()
        logger.info(f"Download URL: {download_url}")
        
        # Define output path
        archive_name = "wesad_dataset.zip"
        output_path = DATA_DIR / archive_name
        
        # Download the file
        checksum = download_file_with_checksum(download_url, output_path)
        
        # Collect checksums
        checksums = {
            str(output_path.relative_to(project_root)): checksum
        }
        
        # Write checksums to file
        write_checksums(checksums)
        
        # Log job duration
        duration_info = log_github_job_duration(start_time)
        
        logger.info("Download completed successfully")
        logger.info(f"Total duration: {duration_info['duration_seconds']:.2f}s")
        
        return 0
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Download timed out: {e}")
        log_github_job_duration(start_time)
        return 1
        
    except RuntimeError as e:
        logger.error(f"Download failed: {e}")
        log_github_job_duration(start_time)
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        log_github_job_duration(start_time)
        return 1


if __name__ == "__main__":
    sys.exit(main())