"""
Dataset download and verification module.
Handles downloading UCI datasets and verifying integrity via checksums.
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project Root (relative to execution context)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    error: Optional[str] = None

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Validate file against expected checksum."""
    if not os.path.exists(file_path):
        return False
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()

def download_from_url(url: str, dest_path: str, expected_checksum: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Download file from URL with optional checksum verification.
    
    Args:
        url: Source URL
        dest_path: Destination file path
        expected_checksum: Optional expected SHA256 checksum for verification
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Setup SSL context (bypass certificate verification for older servers)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Download file
        logger.info(f"Downloading {url} to {dest_path}")
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(request, context=ssl_context, timeout=300) as response:
            with open(dest_path, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        # Verify checksum if provided
        if expected_checksum:
            logger.info(f"Verifying checksum for {dest_path}")
            actual_checksum = compute_file_checksum(dest_path)
            if not validate_checksum(dest_path, expected_checksum):
                error_msg = f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                logger.error(error_msg)
                os.remove(dest_path)
                return False, error_msg
            logger.info(f"Checksum verified: {actual_checksum}")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(error_msg)
        # Clean up partial download if exists
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False, error_msg

def load_checksum_cache(cache_path: str) -> Dict[str, str]:
    """Load checksum cache from JSON file."""
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksum_cache(cache_path: str, checksums: Dict[str, str]):
    """Save checksum cache to JSON file."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def download_electricity_dataset(dest_dir: str) -> DownloadResult:
    """
    Download UCI Electricity Load Diagrams dataset.
    
    Source: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt"
    dest_path = os.path.join(dest_dir, "electricity_load.csv")
    expected_checksum = "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"  # Placeholder, update with real checksum
    
    success, error = download_from_url(url, dest_path, expected_checksum)
    
    return DownloadResult(
        dataset_name="electricity",
        success=success,
        file_path=dest_path if success else None,
        checksum=compute_file_checksum(dest_path) if success else None,
        error=error
    )

def download_traffic_dataset(dest_dir: str) -> DownloadResult:
    """
    Download UCI Traffic dataset.
    
    Source: PEMS-BAY traffic data
    """
    url = "https://pems.dot.ca.gov/data/traffic_data.csv"
    dest_path = os.path.join(dest_dir, "traffic_data.csv")
    expected_checksum = "b2c3d4e5f67890123456789012345678901234567890123456789012345bcde"  # Placeholder, update with real checksum
    
    success, error = download_from_url(url, dest_path, expected_checksum)
    
    return DownloadResult(
        dataset_name="traffic",
        success=success,
        file_path=dest_path if success else None,
        checksum=compute_file_checksum(dest_path) if success else None,
        error=error
    )

def download_synthetic_control_chart_dataset(dest_dir: str) -> DownloadResult:
    """
    Download UCI Synthetic Control Chart Time Series dataset.
    
    Source: https://archive.ics.uci.edu/ml/datasets/Synthetic+Control+Chart+Time+Series
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data"
    dest_path = os.path.join(dest_dir, "synthetic_control.csv")
    expected_checksum = "c3d4e5f67890123456789012345678901234567890123456789012345cdef0"  # Placeholder, update with real checksum
    
    success, error = download_from_url(url, dest_path, expected_checksum)
    
    return DownloadResult(
        dataset_name="synthetic_control_chart",
        success=success,
        file_path=dest_path if success else None,
        checksum=compute_file_checksum(dest_path) if success else None,
        error=error
    )

def verify_dataset_integrity(file_path: str, expected_checksum: str) -> bool:
    """
    Verify dataset integrity against expected checksum.
    
    Args:
        file_path: Path to the dataset file
        expected_checksum: Expected SHA256 checksum
        
    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    try:
        actual_checksum = compute_file_checksum(file_path)
        is_valid = validate_checksum(file_path, expected_checksum)
        
        if is_valid:
            logger.info(f"✓ Integrity verified: {file_path}")
        else:
            logger.error(f"✗ Integrity check failed: {file_path}")
            logger.error(f"  Expected: {expected_checksum}")
            logger.error(f"  Actual:   {actual_checksum}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"✗ Error verifying integrity: {file_path} - {str(e)}")
        return False

def download_all_datasets(dest_dir: str) -> List[DownloadResult]:
    """
    Download all available datasets.
    
    Args:
        dest_dir: Destination directory for downloads
        
    Returns:
        List of DownloadResult objects
    """
    datasets = [
        download_electricity_dataset(dest_dir),
        download_traffic_dataset(dest_dir),
        download_synthetic_control_chart_dataset(dest_dir)
    ]
    
    successful = sum(1 for r in datasets if r.success)
    logger.info(f"Download Summary: {successful}/{len(datasets)} datasets successful")
    
    return datasets

def main():
    """Main entry point for dataset download and verification."""
    dest_dir = "data/raw"
    cache_path = "state/projects/checksum_cache.json"
    
    # Load existing checksum cache
    checksum_cache = load_checksum_cache(cache_path)
    
    # Download datasets
    results = download_all_datasets(dest_dir)
    
    # Verify integrity of downloaded datasets
    integrity_failed = False
    for result in results:
        if result.success and result.file_path:
            expected_checksum = checksum_cache.get(result.dataset_name)
            if expected_checksum:
                if not verify_dataset_integrity(result.file_path, expected_checksum):
                    integrity_failed = True
            else:
                logger.warning(f"No checksum found for {result.dataset_name}, skipping verification")
        
        if not result.success:
            integrity_failed = True
    
    # Update checksum cache with new downloads
    for result in results:
        if result.success and result.checksum:
            checksum_cache[result.dataset_name] = result.checksum
    
    save_checksum_cache(cache_path, checksum_cache)
    
    if integrity_failed:
        logger.error("\n✗ Some datasets failed download or verification.")
        sys.exit(1)
    
    success_count = sum(1 for r in results.values() if r.success)
    if success_count == 0:
        logger.error("No datasets were successfully downloaded.")
        sys.exit(1)
    
    logger.info("All downloads completed.")
    sys.exit(0)

if __name__ == "__main__":
    main()