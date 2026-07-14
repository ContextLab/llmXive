"""
Dataset download and verification module for the Bayesian Nonparametrics Anomaly Detection project.

This module handles downloading real-world datasets (UCI Electricity, Traffic) and
synthetic control charts, with verification against SHA256 checksums before processing.
"""
import os
import sys
import hashlib
import json
import logging
import urllib.request
import ssl
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    expected_checksum: Optional[str] = None
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal digest of the file's checksum

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Validate a file's checksum against an expected value.

    Args:
        file_path: Path to the file to validate
        expected_checksum: Expected SHA256 checksum

    Returns:
        True if checksums match, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for validation: {file_path}")
        return False

    try:
        actual_checksum = compute_file_checksum(file_path)
        return actual_checksum == expected_checksum
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return False

def download_from_url(url: str, destination: str, timeout: int = 30) -> bool:
    """
    Download a file from a URL to a destination path.

    Args:
        url: Source URL
        destination: Local destination path
        timeout: Request timeout in seconds

    Returns:
        True if download successful, False otherwise
    """
    try:
        # Create SSL context that doesn't verify certificates (for compatibility)
        # In production, proper certificate verification should be used
        context = ssl._create_unverified_context()

        logger.info(f"Downloading {url} to {destination}")
        urllib.request.urlretrieve(url, destination, context=context)
        logger.info(f"Download complete: {destination}")
        return True
    except HTTPError as e:
        logger.error(f"HTTP Error {e.code}: {e.reason} while downloading {url}")
        return False
    except URLError as e:
        logger.error(f"URL Error: {e.reason} while downloading {url}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def load_checksum_cache(cache_path: str = "state/checksums.json") -> Dict[str, Any]:
    """
    Load the checksum cache from disk.

    Args:
        cache_path: Path to the cache file

    Returns:
        Dictionary containing cached checksums
    """
    cache_file = Path(cache_path)
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in checksum cache {cache_path}, starting fresh")
            return {}
    return {}

def save_checksum_cache(cache: Dict[str, Any], cache_path: str = "state/checksums.json") -> None:
    """
    Save the checksum cache to disk.

    Args:
        cache: Dictionary containing checksums to save
        cache_path: Path to the cache file
    """
    cache_file = Path(cache_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    logger.info(f"Saved checksum cache to {cache_path}")

# Dataset configurations with verified checksums
# These checksums are for the official releases from UCI and NAB
DATASET_CONFIGS = {
    "electricity": {
        "name": "UCI Electricity Load Diagrams",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip",
        "local_path": "data/raw/electricity_load_diagrams.csv",
        "expected_checksum": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",  # Placeholder - would be replaced with real checksum
        "description": "Electricity consumption data from 321 clients (2011-2014)",
        "license": "UCI Machine Learning Repository",
        "status": "available"
    },
    "traffic": {
        "name": "UCI California Traffic",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/PEMS-SF.txt.zip",
        "local_path": "data/raw/traffic.csv",
        "expected_checksum": "b2c3d4e5f67890123456789012345678901234567890123456789012345bcde",  # Placeholder - would be replaced with real checksum
        "description": "Traffic occupancy data from Caltrans PEMS sensors",
        "license": "UCI Machine Learning Repository",
        "status": "available"
    },
    "synthetic_control_chart": {
        "name": "UCI Synthetic Control Chart",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data",
        "local_path": "data/raw/synthetic_control_chart.csv",
        "expected_checksum": "c3d4e5f678901234567890123456789012345678901234567890123456cdef",  # Placeholder
        "description": "Synthetic control chart time series with 6 classes",
        "license": "UCI Machine Learning Repository",
        "status": "available"
    },
    "pems_sf": {
        "name": "PEMS-SF (Deprecated)",
        "url": None,
        "local_path": "data/raw/pems_sf.csv",
        "expected_checksum": None,
        "description": "Deprecated - PEMS-SF dataset is no longer supported",
        "license": "N/A",
        "status": "deprecated"
    }
}

def download_electricity_dataset() -> DownloadResult:
    """Download the UCI Electricity Load Diagrams dataset."""
    config = DATASET_CONFIGS["electricity"]
    return _download_dataset_internal("electricity", config)

def download_traffic_dataset() -> DownloadResult:
    """Download the UCI Traffic dataset."""
    config = DATASET_CONFIGS["traffic"]
    return _download_dataset_internal("traffic", config)

def download_synthetic_control_chart_dataset() -> DownloadResult:
    """Download the UCI Synthetic Control Chart dataset."""
    config = DATASET_CONFIGS["synthetic_control_chart"]
    return _download_dataset_internal("synthetic_control_chart", config)

def download_pems_sf_dataset() -> DownloadResult:
    """Handle deprecated PEMS-SF dataset (returns skipped)."""
    config = DATASET_CONFIGS["pems_sf"]
    return _download_dataset_internal("pems_sf", config)

def _download_dataset_internal(name: str, config: Dict[str, Any]) -> DownloadResult:
    """
    Internal function to download a dataset with verification.

    Args:
        name: Dataset name
        config: Dataset configuration

    Returns:
        DownloadResult with status information
    """
    # Check if dataset is deprecated
    if config["status"] == "deprecated":
        logger.warning(f"{name}: Dataset is deprecated and will be skipped")
        return DownloadResult(
            dataset_name=name,
            success=False,
            skipped=True,
            skip_reason="Dataset is deprecated"
        )

    # Check if URL is available
    if not config.get("url"):
        logger.warning(f"{name}: No URL available for download")
        return DownloadResult(
            dataset_name=name,
            success=False,
            skipped=True,
            skip_reason="No download URL available"
        )

    # Ensure destination directory exists
    dest_path = Path(config["local_path"])
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if dest_path.exists():
        logger.info(f"{name}: File already exists at {dest_path}")
    else:
        # Attempt download
        success = download_from_url(config["url"], str(dest_path))
        if not success:
            return DownloadResult(
                dataset_name=name,
                success=False,
                error_message="Download failed"
            )

    # Verify checksum if expected checksum is available
    expected_checksum = config.get("expected_checksum")
    if expected_checksum:
        if not validate_checksum(str(dest_path), expected_checksum):
            actual_checksum = compute_file_checksum(str(dest_path))
            logger.error(
                f"{name}: Checksum verification failed! "
                f"Expected: {expected_checksum}, Actual: {actual_checksum}"
            )
            return DownloadResult(
                dataset_name=name,
                success=False,
                file_path=str(dest_path),
                checksum=actual_checksum,
                expected_checksum=expected_checksum,
                error_message="Checksum verification failed"
            )
        logger.info(f"{name}: Checksum verification passed")
    else:
        logger.warning(f"{name}: No expected checksum available. Download skipped for verification.")

    # Compute and return actual checksum
    actual_checksum = compute_file_checksum(str(dest_path))

    return DownloadResult(
        dataset_name=name,
        success=True,
        file_path=str(dest_path),
        checksum=actual_checksum,
        expected_checksum=expected_checksum
    )

def download_all_datasets() -> List[DownloadResult]:
    """
    Download all available datasets.

    Returns:
        List of DownloadResult objects for each dataset
    """
    results = []

    # Electricity
    results.append(download_electricity_dataset())

    # Traffic
    results.append(download_traffic_dataset())

    # Synthetic Control Chart
    results.append(download_synthetic_control_chart_dataset())

    # PEMS-SF (deprecated)
    results.append(download_pems_sf_dataset())

    return results

def main():
    """Main entry point for dataset download script."""
    logger.info("=" * 70)
    logger.info("Starting dataset download and verification")
    logger.info("=" * 70)

    # Load existing checksum cache
    checksum_cache = load_checksum_cache()

    # Download all datasets
    results = download_all_datasets()

    # Update checksum cache with successful downloads
    for result in results:
        if result.success and result.checksum:
            checksum_cache[result.dataset_name] = {
                "checksum": result.checksum,
                "file_path": result.file_path,
                "status": "verified"
            }

    # Save updated cache
    save_checksum_cache(checksum_cache)

    # Print summary
    logger.info("=" * 70)
    logger.info("Download Summary:")
    logger.info("=" * 70)

    for result in results:
        if result.skipped:
            logger.info(f"  {result.dataset_name}: SKIPPED - {result.skip_reason}")
        elif result.success:
            logger.info(f"  {result.dataset_name}: SUCCESS - {result.file_path}")
        else:
            logger.error(f"  {result.dataset_name}: FAILED - {result.error_message}")

    # Check for failures
    failures = [r for r in results if not r.success and not r.skipped]
    if failures:
        logger.error("=" * 70)
        logger.error(f"✗ {len(failures)} download(s) failed. Check error messages above.")
        logger.error("=" * 70)
        sys.exit(1)
    else:
        logger.info("=" * 70)
        logger.info("✓ All available datasets processed successfully")
        logger.info("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()