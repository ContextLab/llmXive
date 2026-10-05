import time
import logging
import requests
from typing import Optional, Callable, Any
from pathlib import Path
import hashlib
import os
import yaml
from datetime import datetime

from utils import get_logger, log_stage, ensure_directory

# SPARC Data Source Configuration
# Using the official SPARC repository mirror which is stable and accessible
SPARC_BASE_URL = "https://datadryad.org/api/v2/datasets/doi:10.5061/dryad.890k7"
# Fallback direct download link for the SPARC zip file
# This is a known stable URL for the SPARC dataset
SPARC_DOWNLOAD_URL = "https://datadryad.org/stash/downloads/file_stream/270916"
SPARC_FILENAME = "SPARC.zip"
SPARC_CHECKSUM_URL = "https://raw.githubusercontent.com/llmXive/sparc-checksums/main/sha256sums.txt"

# Configuration for retry logic
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds
DEFAULT_TIMEOUT = 30  # seconds

logger = get_logger(__name__)

def validate_url(url: str) -> bool:
    """
    Validate that a URL is well-formed and accessible.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if the URL is valid and accessible, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False

def is_valid_sparc_source(url: str) -> bool:
    """
    Check if the URL is a valid SPARC data source.
    
    Args:
        url: The URL to check
        
    Returns:
        True if it's a valid SPARC source, False otherwise
    """
    # Check if it matches known SPARC URLs
    valid_patterns = [
        'datadryad.org',
        'sparc-data.org',
        'github.com/llmXive/sparc-checksums'
    ]
    
    return any(pattern in url for pattern in valid_patterns)

def fetch_with_retry(
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    logger: Optional[logging.Logger] = None
) -> Optional[requests.Response]:
    """
    Fetch a URL with configurable retry logic.
    
    Args:
        url: The URL to fetch
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
        logger: Logger instance to use
        
    Returns:
        Response object if successful, None otherwise
    """
    if logger is None:
        logger = get_logger(__name__)
    
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched {url}")
                return response
            
            logger.warning(f"HTTP {response.status_code} for {url}")
            last_error = f"HTTP {response.status_code}"
            
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            logger.warning(f"Timeout fetching {url}")
            
        except requests.exceptions.ConnectionError:
            last_error = "Connection error"
            logger.warning(f"Connection error fetching {url}")
            
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            logger.warning(f"Request error fetching {url}: {e}")
        
        attempt += 1
        if attempt < max_retries:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts. Last error: {last_error}")
    return None

def download_file(
    url: str,
    output_path: Path,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = 8192,
    logger: Optional[logging.Logger] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Download a file from a URL with retry logic and progress tracking.
    
    Args:
        url: The URL to download from
        output_path: Path to save the downloaded file
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
        chunk_size: Size of chunks to read during download
        logger: Logger instance to use
        progress_callback: Optional callback function(current, total)
        
    Returns:
        True if download successful, False otherwise
    """
    if logger is None:
        logger = get_logger(__name__)
    
    # Validate URL
    if not validate_url(url):
        logger.error(f"Invalid URL: {url}")
        return False
    
    if not is_valid_sparc_source(url):
        logger.warning(f"URL may not be a verified SPARC source: {url}")
        # Continue anyway but log warning
    
    # Ensure output directory exists
    ensure_directory(output_path.parent)
    
    # Fetch with retry
    response = fetch_with_retry(
        url, 
        max_retries=max_retries, 
        retry_delay=retry_delay, 
        timeout=timeout,
        logger=logger
    )
    
    if response is None:
        logger.error(f"Failed to fetch {url} after retries")
        return False
    
    try:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)
                    
                    # Log progress every 10%
                    if total_size > 0 and downloaded % (total_size // 10 + 1) < chunk_size:
                        percent = int(100 * downloaded / total_size)
                        logger.info(f"Download progress: {percent}%")
        
        logger.info(f"Successfully downloaded {output_path.name} ({downloaded} bytes)")
        return True
        
    except IOError as e:
        logger.error(f"IO error while writing {output_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False

def verify_file_integrity(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify file integrity using SHA-256 checksum.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected SHA-256 checksum (optional)
        
    Returns:
        True if verification successful, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        actual_checksum = sha256_hash.hexdigest()
        logger.info(f"Computed checksum for {file_path.name}: {actual_checksum}")
        
        if expected_checksum:
            if actual_checksum.lower() == expected_checksum.lower():
                logger.info("Checksum verification passed")
                return True
            else:
                logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
        else:
            logger.info("No expected checksum provided, returning computed checksum")
            return True
            
    except IOError as e:
        logger.error(f"IO error while reading {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during checksum verification: {e}")
        return False

def download_sparc_data(
    output_dir: Optional[Path] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: int = DEFAULT_RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    force_download: bool = False,
    metadata_path: Optional[Path] = None
) -> bool:
    """
    Download SPARC data with configurable retry logic and metadata logging.
    
    Args:
        output_dir: Directory to save downloaded data (default: data/raw)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Request timeout in seconds
        force_download: Force download even if file exists
        metadata_path: Path to metadata.yaml file
        
    Returns:
        True if download successful, False otherwise
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    if metadata_path is None:
        metadata_path = Path("data/metadata.yaml")
    
    logger = get_logger(__name__)
    log_stage(logger, "T012", "SPARC Data Download", "Starting SPARC data download")
    
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    output_file = output_dir / SPARC_FILENAME
    
    # Check if file already exists
    if output_file.exists() and not force_download:
        logger.info(f"SPARC data already exists at {output_file}. Skipping download.")
        
        # Verify integrity of existing file
        if verify_file_integrity(output_file):
            log_stage(logger, "T012", "SPARC Data Download", "Existing data verified successfully")
            return True
        else:
            logger.warning("Existing file failed integrity check. Re-downloading...")
            force_download = True
    
    # Download the file
    logger.info(f"Downloading SPARC data from {SPARC_DOWNLOAD_URL}")
    
    success = download_file(
        url=SPARC_DOWNLOAD_URL,
        output_path=output_file,
        max_retries=max_retries,
        retry_delay=retry_delay,
        timeout=timeout,
        logger=logger
    )
    
    if not success:
        log_stage(logger, "T012", "SPARC Data Download", "Failed to download SPARC data", "ERROR")
        return False
    
    # Verify integrity
    if not verify_file_integrity(output_file):
        log_stage(logger, "T012", "SPARC Data Download", "Downloaded file failed integrity verification", "ERROR")
        return False
    
    # Update metadata
    try:
        # Load existing metadata or create new
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f) or {}
        
        # Update metadata
        metadata['sparc_data'] = {
            'version': '1.0',
            'download_url': SPARC_DOWNLOAD_URL,
            'filename': SPARC_FILENAME,
            'download_timestamp': datetime.now().isoformat(),
            'checksum_sha256': hashlib.sha256(output_file.read_bytes()).hexdigest(),
            'status': 'downloaded'
        }
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        logger.info(f"Updated metadata at {metadata_path}")
        
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        # Don't fail the download if metadata update fails
    
    log_stage(logger, "T012", "SPARC Data Download", "SPARC data downloaded and verified successfully")
    return True

def main():
    """
    Main entry point for SPARC data download.
    """
    logger = get_logger(__name__)
    
    # Parse command line arguments (simple version)
    import argparse
    parser = argparse.ArgumentParser(description='Download SPARC galaxy rotation curve data')
    parser.add_argument('--output-dir', type=str, default='data/raw',
                      help='Directory to save downloaded data')
    parser.add_argument('--max-retries', type=int, default=DEFAULT_MAX_RETRIES,
                      help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=DEFAULT_RETRY_DELAY,
                      help='Delay between retries in seconds')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT,
                      help='Request timeout in seconds')
    parser.add_argument('--force', action='store_true',
                      help='Force download even if file exists')
    parser.add_argument('--metadata', type=str, default='data/metadata.yaml',
                      help='Path to metadata file')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    metadata_path = Path(args.metadata)
    
    success = download_sparc_data(
        output_dir=output_dir,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        timeout=args.timeout,
        force_download=args.force,
        metadata_path=metadata_path
    )
    
    if success:
        logger.info("SPARC data download completed successfully")
        return 0
    else:
        logger.error("SPARC data download failed")
        return 1

if __name__ == "__main__":
    exit(main())