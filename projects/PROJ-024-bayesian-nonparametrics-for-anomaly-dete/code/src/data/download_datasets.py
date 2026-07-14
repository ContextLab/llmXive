"""
Dataset download and verification module.

Handles downloading datasets from verified sources (UCI, NAB, etc.) and
verifying their integrity against stored checksums before processing.
"""
import os
import sys
import hashlib
import json
import logging
import urllib.request
import ssl
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import yaml

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

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
STATE_DIR = PROJECT_ROOT / 'state'
CHECKSUM_CACHE_FILE = STATE_DIR / 'checksums.json'

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
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    hash_obj = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def validate_checksum(file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Validate file checksum against expected value."""
    if not file_path.exists():
        return False
    
    computed = compute_file_checksum(file_path, algorithm)
    return computed == expected_checksum

def download_from_url(url: str, dest_path: Path, timeout: int = 30) -> bool:
    """Download file from URL to destination path."""
    try:
        # Create SSL context that doesn't verify certificates (for compatibility)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        logger.info(f"Downloading from {url}...")
        urllib.request.urlretrieve(url, dest_path, reporthook=progress_hook)
        logger.info(f"Downloaded to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def progress_hook(block_num, block_size, total_size):
    """Progress hook for urllib."""
    if total_size > 0:
        percent = min(100, (block_num * block_size * 100) // total_size)
        print(f"\rProgress: {percent}%", end='')
    if block_num == 0:
        print()

def load_checksum_cache() -> Dict[str, Any]:
    """Load checksum cache from state file."""
    if CHECKSUM_CACHE_FILE.exists():
        try:
            with open(CHECKSUM_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load checksum cache: {e}")
    return {"datasets": {}}

def save_checksum_cache(cache: Dict[str, Any]) -> None:
    """Save checksum cache to state file."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CHECKSUM_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
        logger.info(f"Saved checksum cache to {CHECKSUM_CACHE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save checksum cache: {e}")

def load_state_config() -> Dict[str, Any]:
    """Load project state configuration."""
    state_file = PROJECT_ROOT / 'state' / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml'
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load state file: {e}")
    return {}

def verify_dataset_integrity(dataset_name: str, file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Verify dataset integrity against stored checksums.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Load state configuration to get expected checksums
    state_config = load_state_config()
    dataset_checksums = state_config.get('dataset_checksums', {})
    
    if dataset_name not in dataset_checksums:
        logger.warning(f"No checksum available for {dataset_name}. Skipping verification.")
        return True, None  # Allow processing if no checksum exists
    
    expected_checksum = dataset_checksums[dataset_name]
    computed_checksum = compute_file_checksum(file_path)
    
    if computed_checksum != expected_checksum:
        return False, f"Checksum mismatch for {dataset_name}. Expected: {expected_checksum}, Got: {computed_checksum}"
    
    logger.info(f"✓ Checksum verified for {dataset_name}")
    return True, None

def download_electricity_dataset() -> DownloadResult:
    """Download UCI Electricity Load Diagrams dataset."""
    dataset_name = "electricity"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt"
    dest_path = DATA_RAW_DIR / "electricity_load.csv"
    
    # Check if already downloaded
    if dest_path.exists():
        is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
        if is_valid:
            checksum = compute_file_checksum(dest_path)
            return DownloadResult(
                dataset_name=dataset_name,
                success=True,
                file_path=str(dest_path),
                checksum=checksum
            )
        else:
            logger.warning(f"Existing file failed verification: {error}")
            os.remove(dest_path)
    
    # Download if checksum not available or download needed
    cache = load_checksum_cache()
    if dataset_name in cache.get('datasets', {}):
        # Try to download
        if download_from_url(url, dest_path):
            is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
            if is_valid:
                checksum = compute_file_checksum(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=str(dest_path),
                    checksum=checksum
                )
            else:
                os.remove(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=False,
                    error_message=error
                )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        skip_reason="No verified checksum available"
    )

def download_traffic_dataset() -> DownloadResult:
    """Download UCI Traffic dataset."""
    dataset_name = "traffic"
    # Using a verified mirror or direct download
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00326/Traffic.txt"
    dest_path = DATA_RAW_DIR / "traffic_data.csv"
    
    if dest_path.exists():
        is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
        if is_valid:
            checksum = compute_file_checksum(dest_path)
            return DownloadResult(
                dataset_name=dataset_name,
                success=True,
                file_path=str(dest_path),
                checksum=checksum
            )
        else:
            os.remove(dest_path)
    
    cache = load_checksum_cache()
    if dataset_name in cache.get('datasets', {}):
        if download_from_url(url, dest_path):
            is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
            if is_valid:
                checksum = compute_file_checksum(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=str(dest_path),
                    checksum=checksum
                )
            else:
                os.remove(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=False,
                    error_message=error
                )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        skip_reason="No verified checksum available"
    )

def download_synthetic_control_chart_dataset() -> DownloadResult:
    """Download Synthetic Control Chart Time Series dataset."""
    dataset_name = "synthetic_control_chart"
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00258/synthetic_control.data"
    dest_path = DATA_RAW_DIR / "synthetic_control_chart.csv"
    
    if dest_path.exists():
        is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
        if is_valid:
            checksum = compute_file_checksum(dest_path)
            return DownloadResult(
                dataset_name=dataset_name,
                success=True,
                file_path=str(dest_path),
                checksum=checksum
            )
        else:
            os.remove(dest_path)
    
    cache = load_checksum_cache()
    if dataset_name in cache.get('datasets', {}):
        if download_from_url(url, dest_path):
            is_valid, error = verify_dataset_integrity(dataset_name, dest_path)
            if is_valid:
                checksum = compute_file_checksum(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=True,
                    file_path=str(dest_path),
                    checksum=checksum
                )
            else:
                os.remove(dest_path)
                return DownloadResult(
                    dataset_name=dataset_name,
                    success=False,
                    error_message=error
                )
    
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        skip_reason="No verified checksum available"
    )

def download_pems_sf_dataset() -> DownloadResult:
    """Download PEMS-SF dataset (deprecated)."""
    dataset_name = "pems_sf"
    logger.warning(f"{dataset_name}: PEMS-SF dataset is deprecated and will be skipped")
    return DownloadResult(
        dataset_name=dataset_name,
        success=False,
        skip_reason="PEMS-SF dataset is deprecated"
    )

def download_all_datasets() -> list:
    """Download all available datasets with checksum verification."""
    results = []
    
    datasets = [
        download_electricity_dataset,
        download_traffic_dataset,
        download_synthetic_control_chart_dataset,
        download_pems_sf_dataset
    ]
    
    for downloader in datasets:
        result = downloader()
        results.append(result)
        if result.success:
            logger.info(f"✓ {result.dataset_name}: Downloaded successfully")
        elif result.skipped:
            logger.warning(f"⚠ {result.dataset_name}: Skipped - {result.skip_reason}")
        else:
            logger.error(f"✗ {result.dataset_name}: Failed - {result.error_message}")
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("=" * 70)
    logger.info("Dataset Download and Verification")
    logger.info("=" * 70)
    
    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download and verify datasets
    results = download_all_datasets()
    
    # Summary
    success_count = sum(1 for r in results if r.success)
    skip_count = sum(1 for r in results if r.skipped)
    fail_count = len(results) - success_count - skip_count
    
    logger.info("=" * 70)
    logger.info("Download Summary:")
    logger.info("=" * 70)
    for result in results:
        if result.success:
            logger.info(f"  {result.dataset_name}: SUCCESS ({result.file_path})")
        elif result.skipped:
            logger.info(f"  {result.dataset_name}: SKIPPED - {result.skip_reason}")
        else:
            logger.info(f"  {result.dataset_name}: FAILED - {result.error_message}")
    
    logger.info("=" * 70)
    logger.info(f"Total: {len(results)} | Success: {success_count} | Skipped: {skip_count} | Failed: {fail_count}")
    logger.info("=" * 70)
    
    # Exit with error if any downloads failed
    if fail_count > 0:
        logger.error("✗ Some downloads failed. Check error messages above.")
        sys.exit(1)
    
    logger.info("✓ All datasets processed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()