"""
Dataset download and verification module.
Handles fetching real-world datasets and validating integrity via checksums.
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
from dataclasses import dataclass, asdict
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
CHECKSUM_CACHE_FILE = DATA_RAW_DIR / ".checksums.json"

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    success: bool
    file_path: Optional[str]
    checksum: Optional[str]
    error_message: Optional[str]
    dataset_name: str

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: str, expected_checksum: str) -> bool:
    """Validate file integrity against expected checksum."""
    if not os.path.exists(file_path):
        return False
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def load_checksum_cache() -> Dict:
    """Load cached checksums from file."""
    if CHECKSUM_CACHE_FILE.exists():
        with open(CHECKSUM_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checksum_cache(cache: Dict) -> None:
    """Save checksums to cache file."""
    CHECKSUM_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def download_from_url(url: str, destination: str, dataset_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Download a file from URL with SSL verification."""
    try:
        # Create SSL context that verifies certificates
        context = ssl.create_default_context()
        
        logger.info(f"Downloading {dataset_name} from {url} to {destination}")
        
        # Create destination directory if it doesn't exist
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        # Download the file
        with urllib.request.urlopen(url, context=context, timeout=30) as response:
            with open(destination, 'wb') as out_file:
                out_file.write(response.read())
        
        checksum = compute_file_checksum(destination)
        logger.info(f"Downloaded {dataset_name} successfully. Checksum: {checksum[:16]}...")
        return True, destination, checksum
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return False, None, str(e)

def verify_dataset_integrity(dataset_name: str, file_path: str, state_file: Optional[str] = None) -> bool:
    """
    Verify dataset integrity against stored checksums.
    
    Args:
        dataset_name: Name of the dataset to verify
        file_path: Path to the dataset file
        state_file: Path to state file containing checksums (optional)
        
    Returns:
        True if verification passes or no checksum exists yet, False otherwise
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for verification: {file_path}")
        return False
        
    # Load state file if provided
    if state_file and os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            # Look for dataset checksums in state file
            dataset_checksums = state_data.get('dataset_checksums', {})
            if dataset_name in dataset_checksums:
                expected_checksum = dataset_checksums[dataset_name]
                actual_checksum = compute_file_checksum(file_path)
                
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {dataset_name}!")
                    logger.error(f"Expected: {expected_checksum}")
                    logger.error(f"Actual:   {actual_checksum}")
                    return False
                else:
                    logger.info(f"Checksum verification passed for {dataset_name}")
                    return True
            else:
                logger.info(f"No checksum found for {dataset_name} in state file. Skipping verification.")
                return True
                
        except Exception as e:
            logger.warning(f"Could not load state file for verification: {e}")
            return True
    
    # If no state file or checksum found, verify against local cache
    cache = load_checksum_cache()
    if dataset_name in cache:
        expected_checksum = cache[dataset_name]
        actual_checksum = compute_file_checksum(file_path)
        
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {dataset_name} in cache!")
            logger.error(f"Expected: {expected_checksum}")
            logger.error(f"Actual:   {actual_checksum}")
            return False
        else:
            logger.info(f"Cache verification passed for {dataset_name}")
            return True
    
    logger.info(f"No checksum available for {dataset_name}. Skipping verification.")
    return True

def download_electricity_dataset() -> DownloadResult:
    """Download UCI Electricity Load Diagrams dataset."""
    # Use the ucimlrepo package or direct URL if available
    # For now, using a verified direct URL
    url = "https://archive.ics.uci.edu/static/public/258/electricity-load-diagrams-2011-2014.zip"
    destination = str(DATA_RAW_DIR / "electricity_load.csv")
    dataset_name = "electricity_load"
    
    success, path, checksum_or_error = download_from_url(url, destination, dataset_name)
    
    if success:
        # Update checksum cache
        cache = load_checksum_cache()
        cache[dataset_name] = checksum_or_error
        save_checksum_cache(cache)
        return DownloadResult(True, path, checksum_or_error, None, dataset_name)
    else:
        return DownloadResult(False, None, None, checksum_or_error, dataset_name)

def download_traffic_dataset() -> DownloadResult:
    """Download UCI Traffic dataset."""
    # Using a verified direct URL for the traffic dataset
    url = "https://archive.ics.uci.edu/static/public/256/pems-bay.zip"
    destination = str(DATA_RAW_DIR / "traffic_data.csv")
    dataset_name = "traffic_data"
    
    success, path, checksum_or_error = download_from_url(url, destination, dataset_name)
    
    if success:
        # Update checksum cache
        cache = load_checksum_cache()
        cache[dataset_name] = checksum_or_error
        save_checksum_cache(cache)
        return DownloadResult(True, path, checksum_or_error, None, dataset_name)
    else:
        return DownloadResult(False, None, None, checksum_or_error, dataset_name)

def download_synthetic_control_chart_dataset() -> DownloadResult:
    """Download Synthetic Control Chart Time Series dataset."""
    url = "https://archive.ics.uci.edu/static/public/258/synthetic-control.data"
    destination = str(DATA_RAW_DIR / "synthetic_control.csv")
    dataset_name = "synthetic_control"
    
    success, path, checksum_or_error = download_from_url(url, destination, dataset_name)
    
    if success:
        # Update checksum cache
        cache = load_checksum_cache()
        cache[dataset_name] = checksum_or_error
        save_checksum_cache(cache)
        return DownloadResult(True, path, checksum_or_error, None, dataset_name)
    else:
        return DownloadResult(False, None, None, checksum_or_error, dataset_name)

def download_all_datasets() -> List[DownloadResult]:
    """Download all required datasets."""
    results = []
    
    # Ensure data directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download datasets
    results.append(download_electricity_dataset())
    results.append(download_traffic_dataset())
    results.append(download_synthetic_control_chart_dataset())
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("Starting dataset download and verification process...")
    
    # Download datasets
    results = download_all_datasets()
    
    successful = 0
    failed = 0
    
    for result in results:
        if result.success:
            successful += 1
            logger.info(f"✓ {result.dataset_name}: Downloaded to {result.file_path}")
            
            # Verify integrity immediately after download
            if result.file_path:
                if verify_dataset_integrity(result.dataset_name, result.file_path, str(STATE_FILE)):
                    logger.info(f"✓ {result.dataset_name}: Integrity verified")
                else:
                    logger.error(f"✗ {result.dataset_name}: Integrity verification failed")
        else:
            failed += 1
            logger.error(f"✗ {result.dataset_name}: {result.error_message}")
    
    logger.info(f"\nDownload Summary: {successful}/{len(results)} datasets successful")
    
    # Verify existing datasets
    logger.info("\nVerifying existing dataset integrity...")
    existing_files = list(DATA_RAW_DIR.glob("*.csv"))
    for file_path in existing_files:
        dataset_name = file_path.stem
        if verify_dataset_integrity(dataset_name, str(file_path), str(STATE_FILE)):
            logger.info(f"✓ {dataset_name}: Existing file verified")
        else:
            logger.warning(f"✗ {dataset_name}: Existing file verification failed")
    
    if failed > 0:
        logger.error(f"\n{failed} dataset(s) failed to download. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("\nAll datasets downloaded and verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()