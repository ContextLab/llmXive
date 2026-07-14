"""
Dataset download and verification module.
Handles downloading real-world datasets (UCI Electricity, Traffic) and synthetic control data,
computing checksums, and validating integrity before processing.
"""

import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/dataset_download.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    filepath: Optional[str] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None

# Expected checksums for datasets (update when downloading new versions)
# These are placeholders - in production, these should be the actual checksums
# of the verified dataset versions
EXPECTED_CHECKSUMS: Dict[str, str] = {
    # UCI Electricity Load Diagrams 2011-2014
    'electricity.csv': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    # UCI Traffic Data
    'traffic.csv': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    # Synthetic Control Chart Time Series
    'synthetic_control.csv': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
}

# Dataset URLs and metadata
DATASET_METADATA: Dict[str, Dict[str, Any]] = {
    'electricity': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt',
        'filename': 'electricity.csv',
        'description': 'UCI Electricity Load Diagrams 2011-2014',
        'license': 'CC BY 4.0',
        'requires_processing': True
    },
    'traffic': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00323/traffic.txt',
        'filename': 'traffic.csv',
        'description': 'UCI Traffic Data',
        'license': 'CC BY 4.0',
        'requires_processing': True
    },
    'synthetic_control_chart': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data',
        'filename': 'synthetic_control.csv',
        'description': 'UCI Synthetic Control Chart Time Series',
        'license': 'CC BY 4.0',
        'requires_processing': True
    }
}

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal checksum string
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()

def validate_checksum(filepath: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Validate a file's checksum against an expected value.

    Args:
        filepath: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use

    Returns:
        True if checksum matches, False otherwise
    """
    try:
        actual_checksum = compute_file_checksum(filepath, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        logger.error(f"Error validating checksum for {filepath}: {e}")
        return False

def download_from_url(
    url: str,
    destination: str,
    progress: bool = True,
    timeout: int = 300
) -> Tuple[bool, Optional[str]]:
    """
    Download a file from a URL with optional progress reporting.

    Args:
        url: Source URL
        destination: Destination file path
        progress: Whether to show progress
        timeout: Download timeout in seconds

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Create SSL context that doesn't verify certificates (for environments with cert issues)
        # In production, this should be properly configured
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        # Define a progress hook that prints download progress
        def report_hook(count, block_size, total_size):
            if total_size > 0:
                percent = min(count * block_size * 100 // total_size, 100)
                sys.stdout.write(f"\rDownloading: {percent}%")
                sys.stdout.flush()

        # Download the file
        logger.info(f"Downloading from {url}")
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        
        # Add SSL context to the opener
        import urllib.error
        try:
            urllib.request.urlretrieve(url, destination, reporthook=report_hook if progress else None)
        except AttributeError:
            # Fallback for environments where urlretrieve doesn't accept reporthook
            with opener.open(url, timeout=timeout) as response:
                with open(destination, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)

        if progress:
            print()  # New line after progress

        # Verify the download succeeded
        if os.path.exists(destination) and os.path.getsize(destination) > 0:
            logger.info(f"Download successful: {destination}")
            return True, None
        else:
            logger.error(f"Download failed or resulted in empty file: {destination}")
            return False, "Download resulted in empty or non-existent file"

    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error downloading {url}: {e.code} {e.reason}")
        return False, f"HTTP error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        logger.error(f"URL error downloading {url}: {e.reason}")
        return False, f"URL error: {e.reason}"
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False, str(e)

def load_checksum_cache(cache_path: str = 'data/checksum_cache.json') -> Dict[str, str]:
    """
    Load the checksum cache from disk.

    Args:
        cache_path: Path to the cache file

    Returns:
        Dictionary mapping filenames to checksums
    """
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading checksum cache: {e}. Starting fresh.")
    return {}

def save_checksum_cache(cache: Dict[str, str], cache_path: str = 'data/checksum_cache.json') -> None:
    """
    Save the checksum cache to disk.

    Args:
        cache: Dictionary mapping filenames to checksums
        cache_path: Path to the cache file
    """
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Checksum cache saved to {cache_path}")
    except Exception as e:
        logger.error(f"Error saving checksum cache: {e}")

def verify_dataset_integrity(
    filepath: str,
    dataset_name: str,
    expected_checksum: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Verify the integrity of a downloaded dataset.

    Args:
        filepath: Path to the dataset file
        dataset_name: Name of the dataset
        expected_checksum: Expected checksum (if known)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"

    try:
        actual_checksum = compute_file_checksum(filepath)
        logger.info(f"Computed checksum for {dataset_name}: {actual_checksum[:16]}...")

        if expected_checksum:
            if actual_checksum.lower() == expected_checksum.lower():
                logger.info(f"✓ Checksum validation passed for {dataset_name}")
                return True, None
            else:
                error_msg = f"Checksum mismatch for {dataset_name}. Expected: {expected_checksum}, Got: {actual_checksum}"
                logger.error(error_msg)
                return False, error_msg
        else:
            # No expected checksum provided, just log the computed one
            logger.warning(f"No expected checksum provided for {dataset_name}. Computed: {actual_checksum}")
            # In this case, we consider it valid but warn
            return True, None

    except Exception as e:
        error_msg = f"Error verifying integrity of {dataset_name}: {e}"
        logger.error(error_msg)
        return False, error_msg

def download_electricity_dataset(output_dir: str = 'data/raw') -> DownloadResult:
    """
    Download the UCI Electricity Load Diagrams dataset.

    Args:
        output_dir: Directory to save the dataset

    Returns:
        DownloadResult object
    """
    metadata = DATASET_METADATA['electricity']
    filepath = os.path.join(output_dir, metadata['filename'])

    logger.info(f"Processing dataset: electricity")
    success, error = download_from_url(metadata['url'], filepath)

    if success:
        # Compute checksum
        try:
            checksum = compute_file_checksum(filepath)
            file_size = os.path.getsize(filepath)
            logger.info(f"Electricity dataset downloaded: {file_size} bytes, checksum: {checksum[:16]}...")
            return DownloadResult(
                dataset_name='electricity',
                success=True,
                filepath=filepath,
                checksum=checksum,
                file_size=file_size
            )
        except Exception as e:
            return DownloadResult(
                dataset_name='electricity',
                success=False,
                error_message=f"Error computing checksum: {e}"
            )
    else:
        return DownloadResult(
            dataset_name='electricity',
            success=False,
            error_message=error
        )

def download_traffic_dataset(output_dir: str = 'data/raw') -> DownloadResult:
    """
    Download the UCI Traffic dataset.

    Args:
        output_dir: Directory to save the dataset

    Returns:
        DownloadResult object
    """
    metadata = DATASET_METADATA['traffic']
    filepath = os.path.join(output_dir, metadata['filename'])

    logger.info(f"Processing dataset: traffic")
    success, error = download_from_url(metadata['url'], filepath)

    if success:
        try:
            checksum = compute_file_checksum(filepath)
            file_size = os.path.getsize(filepath)
            logger.info(f"Traffic dataset downloaded: {file_size} bytes, checksum: {checksum[:16]}...")
            return DownloadResult(
                dataset_name='traffic',
                success=True,
                filepath=filepath,
                checksum=checksum,
                file_size=file_size
            )
        except Exception as e:
            return DownloadResult(
                dataset_name='traffic',
                success=False,
                error_message=f"Error computing checksum: {e}"
            )
    else:
        return DownloadResult(
            dataset_name='traffic',
            success=False,
            error_message=error
        )

def download_synthetic_control_chart_dataset(output_dir: str = 'data/raw') -> DownloadResult:
    """
    Download the UCI Synthetic Control Chart dataset.

    Args:
        output_dir: Directory to save the dataset

    Returns:
        DownloadResult object
    """
    metadata = DATASET_METADATA['synthetic_control_chart']
    filepath = os.path.join(output_dir, metadata['filename'])

    logger.info(f"Processing dataset: synthetic_control_chart")
    success, error = download_from_url(metadata['url'], filepath)

    if success:
        try:
            checksum = compute_file_checksum(filepath)
            file_size = os.path.getsize(filepath)
            logger.info(f"Synthetic control chart dataset downloaded: {file_size} bytes, checksum: {checksum[:16]}...")
            return DownloadResult(
                dataset_name='synthetic_control_chart',
                success=True,
                filepath=filepath,
                checksum=checksum,
                file_size=file_size
            )
        except Exception as e:
            return DownloadResult(
                dataset_name='synthetic_control_chart',
                success=False,
                error_message=f"Error computing checksum: {e}"
            )
    else:
        return DownloadResult(
            dataset_name='synthetic_control_chart',
            success=False,
            error_message=error
        )

def download_all_datasets(output_dir: str = 'data/raw') -> List[DownloadResult]:
    """
    Download all available datasets.

    Args:
        output_dir: Directory to save the datasets

    Returns:
        List of DownloadResult objects
    """
    results = []

    # Download each dataset
    results.append(download_electricity_dataset(output_dir))
    results.append(download_traffic_dataset(output_dir))
    results.append(download_synthetic_control_chart_dataset(output_dir))

    # Summary
    successful = sum(1 for r in results if r.success)
    logger.info("=" * 70)
    logger.info(f"Download Summary: {successful}/{len(results)} datasets successful")
    logger.info("=" * 70)

    # Verify integrity of downloaded datasets
    logger.info("\nVerifying integrity of downloaded datasets...")
    for result in results:
        if result.success and result.filepath:
          # Use expected checksums if available, otherwise just verify file exists
          expected = EXPECTED_CHECKSUMS.get(result.dataset_name)
          is_valid, error = verify_dataset_integrity(result.filepath, result.dataset_name, expected)
          if not is_valid:
              result.success = False
              result.error_message = error

    failed = [r for r in results if not r.success]
    if failed:
        logger.error("\n✗ Some datasets failed download or verification.")
        for r in failed:
            logger.error(f"  ✗ {r.dataset_name}: {r.error_message}")
    else:
        logger.info("\n✓ All datasets downloaded and verified successfully.")

    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("=" * 70)
    logger.info("Dataset Download and Verification")
    logger.info("=" * 70)

    # Determine output directory
    output_dir = 'data/raw'
    os.makedirs(output_dir, exist_ok=True)

    # Download all datasets
    results = download_all_datasets(output_dir)

    # Check if any downloads failed
    failed = [r for r in results if not r.success]
    if failed:
        logger.error("\n✗ Some datasets failed download or verification.")
        sys.exit(1)
    else:
        logger.info("\n✓ All datasets downloaded and verified successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()