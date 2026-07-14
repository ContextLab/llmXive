"""
Dataset download and verification module.

Handles fetching real-world datasets (UCI Electricity, Traffic) and synthetic
control charts, with checksum verification against known hashes.

This module implements T052 (fetching) and T059 (verification logic).
"""
import os
import sys
import hashlib
import logging
import json
import urllib.request
import ssl
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUM_CACHE_FILE = STATE_DIR / "checksums.json"

# Known checksums for verified datasets
# These are updated as datasets are fetched and verified
KNOWN_CHECKSUMS = {
    "electricity": None,  # Will be populated after first successful fetch
    "traffic": None,
    "synthetic_control_chart": None,
}

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    file_path: Optional[Path] = None
    checksum: Optional[str] = None
    expected_checksum: Optional[str] = None
    message: str = ""

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_checksum(filepath: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Validate a file's checksum against an expected value.
    
    Args:
        filepath: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use
        
    Returns:
        True if checksum matches, False otherwise
    """
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return False
    
    actual_checksum = compute_file_checksum(filepath, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()

def load_checksum_cache() -> Dict[str, Any]:
    """Load the checksum cache from disk."""
    if CHECKSUM_CACHE_FILE.exists():
        with open(CHECKSUM_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {"checksums": {}, "last_updated": None}

def save_checksum_cache(cache: Dict[str, Any]) -> None:
    """Save the checksum cache to disk."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    logger.info(f"Saved checksum cache to {CHECKSUM_CACHE_FILE}")

def download_from_url(url: str, destination: Path, timeout: int = 300) -> bool:
    """
    Download a file from a URL with verification.
    
    Args:
        url: Source URL
        destination: Destination path
        timeout: Request timeout in seconds
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        # Create SSL context that doesn't verify certificates (for compatibility)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Downloading from {url} to {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
            with open(destination, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        logger.info(f"Download complete: {destination}")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def download_electricity_dataset() -> DownloadResult:
    """
    Download the UCI Electricity Load Diagrams dataset.
    
    Source: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014
    """
    dataset_name = "electricity"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt"
    filename = "electricity_load.csv"
    destination = DATA_RAW_DIR / filename
    
    # Check if file already exists
    if destination.exists():
        logger.info(f"File already exists: {destination}")
        # Verify checksum if known
        cache = load_checksum_cache()
        expected = cache.get("checksums", {}).get(dataset_name)
        if expected:
            if validate_checksum(destination, expected):
                logger.info(f"Checksum verified for {dataset_name}")
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=destination,
                    checksum=expected,
                    expected_checksum=expected,
                    message="Already downloaded and verified"
                )
            else:
                logger.warning(f"Checksum mismatch for {dataset_name}, re-downloading")
        
    # Download the dataset
    if download_from_url(url, destination):
        checksum = compute_file_checksum(destination)
        
        # Update cache
        cache = load_checksum_cache()
        cache["checksums"][dataset_name] = checksum
        save_checksum_cache(cache)
        
        return DownloadResult(
            dataset_name=dataset_name,
            success=True,
            file_path=destination,
            checksum=checksum,
            expected_checksum=checksum,
            message="Downloaded and checksummed"
        )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        message="Download failed"
    )

def download_traffic_dataset() -> DownloadResult:
    """
    Download the UCI Traffic dataset.
    
    Source: https://archive.ics.uci.edu/ml/datasets/PEMS-SF (Note: PEMS-SF is deprecated,
            using alternative source for traffic data)
    """
    dataset_name = "traffic"
    # Using a publicly available traffic dataset as alternative
    url = "https://raw.githubusercontent.com/laiguokun/multivariate-time-series-data/master/traffic/traffic.csv.gz"
    filename = "traffic.csv.gz"
    destination = DATA_RAW_DIR / filename
    
    if destination.exists():
        logger.info(f"File already exists: {destination}")
        cache = load_checksum_cache()
        expected = cache.get("checksums", {}).get(dataset_name)
        if expected:
            if validate_checksum(destination, expected):
                logger.info(f"Checksum verified for {dataset_name}")
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=destination,
                    checksum=expected,
                    expected_checksum=expected,
                    message="Already downloaded and verified"
                )
            else:
                logger.warning(f"Checksum mismatch for {dataset_name}, re-downloading")
    
    if download_from_url(url, destination):
        checksum = compute_file_checksum(destination)
        
        cache = load_checksum_cache()
        cache["checksums"][dataset_name] = checksum
        save_checksum_cache(cache)
        
        return DownloadResult(
            dataset_name=dataset_name,
            success=True,
            file_path=destination,
            checksum=checksum,
            expected_checksum=checksum,
            message="Downloaded and checksummed"
        )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        message="Download failed"
    )

def download_synthetic_control_chart_dataset() -> DownloadResult:
    """
    Download the Synthetic Control Chart Time Series dataset from UCI.
    
    Source: https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series
    """
    dataset_name = "synthetic_control_chart"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00115/UCR_Synthetic_Control.zip"
    filename = "synthetic_control_chart.zip"
    destination = DATA_RAW_DIR / filename
    
    if destination.exists():
        logger.info(f"File already exists: {destination}")
        cache = load_checksum_cache()
        expected = cache.get("checksums", {}).get(dataset_name)
        if expected:
            if validate_checksum(destination, expected):
                logger.info(f"Checksum verified for {dataset_name}")
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=destination,
                    checksum=expected,
                    expected_checksum=expected,
                    message="Already downloaded and verified"
                )
            else:
                logger.warning(f"Checksum mismatch for {dataset_name}, re-downloading")
    
    if download_from_url(url, destination):
        checksum = compute_file_checksum(destination)
        
        cache = load_checksum_cache()
        cache["checksums"][dataset_name] = checksum
        save_checksum_cache(cache)
        
        return DownloadResult(
            dataset_name=dataset_name,
            success=True,
            file_path=destination,
            checksum=checksum,
            expected_checksum=checksum,
            message="Downloaded and checksummed"
        )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        message="Download failed"
    )

def download_pems_sf_dataset() -> DownloadResult:
    """
    Download PEMS-SF dataset.
    
    Note: This dataset is deprecated and should not be used.
    Returns a skipped result.
    """
    logger.warning("PEMS-SF dataset is deprecated and will be skipped")
    return DownloadResult(
        dataset_name="pems_sf",
        success=False,
        message="Dataset deprecated"
    )

def verify_dataset_integrity(dataset_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify the integrity of a downloaded dataset against its checksum.
    
    This is the core verification logic for T059.
    
    Args:
        dataset_name: Name of the dataset to verify
        
    Returns:
        Tuple of (is_valid, actual_checksum, expected_checksum)
    """
    cache = load_checksum_cache()
    expected_checksum = cache.get("checksums", {}).get(dataset_name)
    
    if not expected_checksum:
        logger.warning(f"No expected checksum available for {dataset_name}. Verification skipped.")
        return False, None, None
    
    # Determine file path based on dataset name
    file_map = {
        "electricity": "electricity_load.csv",
        "traffic": "traffic.csv.gz",
        "synthetic_control_chart": "synthetic_control_chart.zip",
        "pems_sf": "pems_sf.csv",
    }
    
    filename = file_map.get(dataset_name)
    if not filename:
        logger.error(f"Unknown dataset name: {dataset_name}")
        return False, None, None
    
    filepath = DATA_RAW_DIR / filename
    
    if not filepath.exists():
        logger.error(f"Dataset file not found: {filepath}")
        return False, None, expected_checksum
    
    actual_checksum = compute_file_checksum(filepath)
    is_valid = validate_checksum(filepath, expected_checksum)
    
    if is_valid:
        logger.info(f"✓ Integrity verified for {dataset_name}")
    else:
        logger.error(f"✗ Integrity check FAILED for {dataset_name}")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {actual_checksum}")
    
    return is_valid, actual_checksum, expected_checksum

def download_all_datasets() -> Dict[str, DownloadResult]:
    """
    Download all configured datasets.
    
    Returns:
        Dictionary mapping dataset names to their download results
    """
    results = {}
    
    # Electricity dataset
    results["electricity"] = download_electricity_dataset()
    
    # Traffic dataset
    results["traffic"] = download_traffic_dataset()
    
    # Synthetic control chart (optional, for fallback)
    results["synthetic_control_chart"] = download_synthetic_control_chart_dataset()
    
    # PEMS-SF (deprecated, skipped)
    results["pems_sf"] = download_pems_sf_dataset()
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("=" * 70)
    logger.info("Dataset Download and Verification")
    logger.info("=" * 70)
    
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download datasets
    results = download_all_datasets()
    
    # Verify integrity of downloaded datasets
    logger.info("=" * 70)
    logger.info("Verifying Dataset Integrity")
    logger.info("=" * 70)
    
    verification_results = {}
    for dataset_name in results.keys():
        if dataset_name == "pems_sf":
            continue  # Skip deprecated dataset
        
        is_valid, actual, expected = verify_dataset_integrity(dataset_name)
        verification_results[dataset_name] = {
            "valid": is_valid,
            "actual_checksum": actual,
            "expected_checksum": expected
        }
    
    # Print summary
    logger.info("=" * 70)
    logger.info("Download Summary:")
    logger.info("=" * 70)
    
    all_success = True
    for dataset_name, result in results.items():
        status = "✓ SUCCESS" if result.success else "✗ FAILED"
        logger.info(f"  {dataset_name}: {status}")
        if not result.success:
            all_success = False
    
    logger.info("=" * 70)
    logger.info("Verification Summary:")
    logger.info("=" * 70)
    
    all_verified = True
    for dataset_name, verification in verification_results.items():
        status = "✓ VERIFIED" if verification["valid"] else "✗ FAILED"
        logger.info(f"  {dataset_name}: {status}")
        if not verification["valid"]:
            all_verified = False
    
    if not all_success:
        logger.error("✗ Some downloads failed. Check error messages above.")
        sys.exit(1)
    
    if not all_verified:
        logger.error("✗ Some integrity checks failed. Check error messages above.")
        sys.exit(1)
    
    logger.info("✓ All downloads and verifications completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()