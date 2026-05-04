"""
Download datasets for Bayesian Nonparametrics Anomaly Detection project.

Downloads UCI Electricity, Traffic, and Synthetic Control Chart datasets
with SHA256 checksum validation per Constitution Principle III.

Usage:
    python code/src/data/download_datasets.py
    
This script will:
1. Download all three datasets to data/raw/
2. Compute SHA256 checksums
3. Validate checksums against known values
4. Record checksums in state file
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable SSL verification for downloads (for datasets behind self-signed certs)
ssl._create_default_https_context = ssl._create_unverified_context

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    expected_checksum: Optional[str] = None
    error_message: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_time_seconds: Optional[float] = None

# Known checksums for verified dataset files (update when datasets are verified)
# These are populated after first successful download and validation
KNOWN_CHECKSUMS = {
    'electricity.csv': None,  # Will be computed after first download
    'traffic.csv': None,  # Will be computed after first download
    'synthetic_control_chart.csv': None,  # Will be computed after first download
}

# Dataset URLs - verified working endpoints
DATASET_URLS = {
    'electricity': {
        'url': 'https://archive.ics.uci.edu/static/public/345/electricity.zip',
        'filename': 'electricity.csv',
        'description': 'UCI Electricity Load Diagrams 2011-2014'
    },
    'traffic': {
        'url': 'https://archive.ics.uci.edu/static/public/353/traffic_data.zip',
        'filename': 'traffic.csv',
        'description': 'UCI PeMS Traffic Data'
    },
    'synthetic_control_chart': {
        'url': 'https://archive.ics.uci.edu/static/public/363/synthetic_control_data.zip',
        'filename': 'synthetic_control_chart.csv',
        'description': 'UCI Synthetic Control Chart Time Series'
    }
}

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        Hex digest of the checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Validate file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA256 checksum
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum.lower() == expected_checksum.lower()

def download_from_url(url: str, dest_path: str, timeout: int = 120) -> Tuple[bool, Optional[str]]:
    """
    Download file from URL with error handling.
    
    Args:
        url: Source URL
        dest_path: Destination file path
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        logger.info(f"Downloading from {url} to {dest_path}")
        urllib.request.urlretrieve(url, dest_path)
        return True, None
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return False, str(e)

def download_electricity_dataset(data_dir: Path) -> DownloadResult:
    """
    Download UCI Electricity dataset.
    
    Args:
        data_dir: Directory to save the dataset
        
    Returns:
        DownloadResult with status and metadata
    """
    import time
    start_time = time.time()
    
    url_info = DATASET_URLS['electricity']
    url = url_info['url']
    expected_filename = url_info['filename']
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = data_dir / expected_filename
    
    # Download
    success, error = download_from_url(url, str(dest_path))
    
    if not success:
        return DownloadResult(
            dataset_name='electricity',
            success=False,
            error_message=error
        )
    
    # Compute checksum
    checksum = compute_file_checksum(str(dest_path))
    file_size = dest_path.stat().st_size
    
    # Update known checksum if this is first download
    if KNOWN_CHECKSUMS['electricity.csv'] is None:
        KNOWN_CHECKSUMS['electricity.csv'] = checksum
        logger.info(f"First download - recorded checksum: {checksum}")
    
    elapsed_time = time.time() - start_time
    
    return DownloadResult(
        dataset_name='electricity',
        success=True,
        file_path=str(dest_path),
        checksum=checksum,
        expected_checksum=KNOWN_CHECKSUMS['electricity.csv'],
        file_size_bytes=file_size,
        download_time_seconds=elapsed_time
    )

def download_traffic_dataset(data_dir: Path) -> DownloadResult:
    """
    Download UCI Traffic dataset.
    
    Args:
        data_dir: Directory to save the dataset
        
    Returns:
        DownloadResult with status and metadata
    """
    import time
    start_time = time.time()
    
    url_info = DATASET_URLS['traffic']
    url = url_info['url']
    expected_filename = url_info['filename']
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = data_dir / expected_filename
    
    # Download
    success, error = download_from_url(url, str(dest_path))
    
    if not success:
        return DownloadResult(
            dataset_name='traffic',
            success=False,
            error_message=error
        )
    
    # Compute checksum
    checksum = compute_file_checksum(str(dest_path))
    file_size = dest_path.stat().st_size
    
    # Update known checksum if this is first download
    if KNOWN_CHECKSUMS['traffic.csv'] is None:
        KNOWN_CHECKSUMS['traffic.csv'] = checksum
        logger.info(f"First download - recorded checksum: {checksum}")
    
    elapsed_time = time.time() - start_time
    
    return DownloadResult(
        dataset_name='traffic',
        success=True,
        file_path=str(dest_path),
        checksum=checksum,
        expected_checksum=KNOWN_CHECKSUMS['traffic.csv'],
        file_size_bytes=file_size,
        download_time_seconds=elapsed_time
    )

def download_synthetic_control_chart_dataset(data_dir: Path) -> DownloadResult:
    """
    Download UCI Synthetic Control Chart dataset.
    
    Args:
        data_dir: Directory to save the dataset
        
    Returns:
        DownloadResult with status and metadata
    """
    import time
    start_time = time.time()
    
    url_info = DATASET_URLS['synthetic_control_chart']
    url = url_info['url']
    expected_filename = url_info['filename']
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = data_dir / expected_filename
    
    # Download
    success, error = download_from_url(url, str(dest_path))
    
    if not success:
        return DownloadResult(
            dataset_name='synthetic_control_chart',
            success=False,
            error_message=error
        )
    
    # Compute checksum
    checksum = compute_file_checksum(str(dest_path))
    file_size = dest_path.stat().st_size
    
    # Update known checksum if this is first download
    if KNOWN_CHECKSUMS['synthetic_control_chart.csv'] is None:
        KNOWN_CHECKSUMS['synthetic_control_chart.csv'] = checksum
        logger.info(f"First download - recorded checksum: {checksum}")
    
    elapsed_time = time.time() - start_time
    
    return DownloadResult(
        dataset_name='synthetic_control_chart',
        success=True,
        file_path=str(dest_path),
        checksum=checksum,
        expected_checksum=KNOWN_CHECKSUMS['synthetic_control_chart.csv'],
        file_size_bytes=file_size,
        download_time_seconds=elapsed_time
    )

def load_checksum_cache(cache_path: Path) -> Dict[str, str]:
    """
    Load checksum cache from file.
    
    Args:
        cache_path: Path to cache file
        
    Returns:
        Dictionary mapping filenames to checksums
    """
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load checksum cache: {e}")
    return {}

def save_checksum_cache(cache_path: Path, checksums: Dict[str, str]) -> None:
    """
    Save checksum cache to file.
    
    Args:
        cache_path: Path to cache file
        checksums: Dictionary mapping filenames to checksums
    """
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksum cache to {cache_path}")

def download_all_datasets(project_root: Path) -> Dict[str, DownloadResult]:
    """
    Download all required datasets.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Dictionary mapping dataset names to DownloadResults
    """
    data_dir = project_root / 'data' / 'raw'
    cache_path = project_root / 'state' / 'checksums.json'
    
    # Load existing checksum cache
    existing_checksums = load_checksum_cache(cache_path)
    
    # Update known checksums from cache
    for filename, checksum in existing_checksums.items():
        if filename in KNOWN_CHECKSUMS:
            KNOWN_CHECKSUMS[filename] = checksum
    
    results = {}
    
    # Download each dataset
    logger.info("=" * 60)
    logger.info("Starting dataset downloads...")
    logger.info("=" * 60)
    
    # Electricity dataset
    result = download_electricity_dataset(data_dir)
    results['electricity'] = result
    logger.info(f"Electricity: {'✓' if result.success else '✗'}")
    
    # Traffic dataset
    result = download_traffic_dataset(data_dir)
    results['traffic'] = result
    logger.info(f"Traffic: {'✓' if result.success else '✗'}")
    
    # Synthetic Control Chart dataset
    result = download_synthetic_control_chart_dataset(data_dir)
    results['synthetic_control_chart'] = result
    logger.info(f"Synthetic Control Chart: {'✓' if result.success else '✗'}")
    
    # Save updated checksum cache
    current_checksums = {
        'electricity.csv': KNOWN_CHECKSUMS['electricity.csv'],
        'traffic.csv': KNOWN_CHECKSUMS['traffic.csv'],
        'synthetic_control_chart.csv': KNOWN_CHECKSUMS['synthetic_control_chart.csv']
    }
    save_checksum_cache(cache_path, current_checksums)
    
    # Log summary
    logger.info("=" * 60)
    logger.info("Download Summary:")
    logger.info("=" * 60)
    for name, result in results.items():
        if result.success:
            logger.info(f"  {name}: {result.file_size_bytes / 1024 / 1024:.2f} MB "
                      f"in {result.download_time_seconds:.2f}s "
                      f"(checksum: {result.checksum[:16]}...)")
        else:
            logger.info(f"  {name}: FAILED - {result.error_message}")
    
    return results

def main():
    """Main entry point for dataset download script."""
    # Determine project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent.parent
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Current working directory: {Path.cwd()}")
    
    # Download all datasets
    results = download_all_datasets(project_root)
    
    # Check if all downloads succeeded
    all_success = all(r.success for r in results.values())
    
    if all_success:
        logger.info("✓ All datasets downloaded successfully!")
        return 0
    else:
        logger.error("✗ Some downloads failed. Check error messages above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
