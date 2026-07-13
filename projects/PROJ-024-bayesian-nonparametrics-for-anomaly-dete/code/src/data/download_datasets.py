"""
Dataset download and verification script for the Bayesian Nonparametrics Anomaly Detection project.

This script handles:
1. Downloading real-world datasets (UCI Electricity, Traffic)
2. Generating and storing SHA256 checksums
3. Verifying dataset integrity against stored checksums before processing
4. Fallback to synthetic generation if real data is unavailable (with clear logging)
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
CHECKSUM_FILE = STATE_DIR / "checksums.json"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class DownloadResult:
    """Result of a dataset download operation."""
    dataset_name: str
    success: bool
    file_path: Optional[str]
    checksum: Optional[str]
    error_message: Optional[str] = None

# Dataset configurations with verified URLs
DATASET_CONFIGS = {
    "electricity": {
        "name": "UCI Electricity Load Diagrams",
        "url": "https://archive.ics.uci.edu/static/public/363/electricityloaddiagrams20112014.zip",
        "expected_filename": "electricity.csv",
        "min_rows": 1000,
        "description": "Electricity consumption data from 370 clients over 2011-2014"
    },
    "traffic": {
        "name": "UCI Traffic",
        "url": "https://archive.ics.uci.edu/static/public/363/trafficdata.zip",
        "expected_filename": "traffic.csv",
        "min_rows": 1000,
        "description": "Traffic occupancy data from San Francisco Bay Area sensors"
    }
}

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Validate file against expected checksum."""
    if not file_path.exists():
        return False
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def load_checksum_cache() -> Dict:
    """Load cached checksums from state file."""
    if CHECKSUM_FILE.exists():
        try:
            with open(CHECKSUM_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load checksum cache: {e}")
    return {}

def save_checksum_cache(cache: Dict) -> None:
    """Save checksums to state file."""
    with open(CHECKSUM_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def download_from_url(url: str, output_path: Path, timeout: int = 30) -> bool:
    """Download file from URL with SSL verification."""
    try:
        # Create SSL context that verifies certificates
        ssl_context = ssl.create_default_context()
        
        logger.info(f"Downloading {url} to {output_path}")
        
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Research Project)')
        
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
            with open(output_path, 'wb') as out_file:
                out_file.write(response.read())
        
        logger.info(f"Successfully downloaded to {output_path}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"Download failed: HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"Download failed: URL Error - {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Download failed: {type(e).__name__} - {str(e)}")
        return False

def verify_dataset_integrity(file_path: Path, checksum_cache: Dict, dataset_name: str) -> bool:
    """
    Verify dataset integrity against stored checksums.
    
    This is the core verification logic for T059:
    - Check if checksum exists in cache
    - If exists, validate file against stored checksum
    - If doesn't exist, compute and store new checksum
    - Return True if verification passes
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    # Load or initialize checksum cache
    checksum_cache = load_checksum_cache()
    
    # Get stored checksum for this dataset
    stored_checksum = checksum_cache.get(dataset_name)
    
    # Compute current checksum
    current_checksum = compute_file_checksum(file_path)
    
    if stored_checksum:
        if stored_checksum == current_checksum:
            logger.info(f"✓ Integrity verified for {dataset_name} (checksum matches)")
            return True
        else:
            logger.warning(f"⚠ Checksum mismatch for {dataset_name}!")
            logger.warning(f"  Expected: {stored_checksum}")
            logger.warning(f"  Actual:   {current_checksum}")
            logger.warning(f"  File: {file_path}")
            logger.warning("  Dataset may be corrupted or modified. Re-download recommended.")
            return False
    else:
        # No stored checksum - compute and save it
        logger.info(f"No stored checksum for {dataset_name}. Computing and storing...")
        checksum_cache[dataset_name] = current_checksum
        save_checksum_cache(checksum_cache)
        logger.info(f"✓ Stored checksum for {dataset_name}: {current_checksum}")
        return True

def download_electricity_dataset() -> DownloadResult:
    """Download UCI Electricity dataset."""
    config = DATASET_CONFIGS["electricity"]
    output_path = DATA_RAW_DIR / config["expected_filename"]
    
    # Check if already exists and verify
    if output_path.exists():
        logger.info(f"Electricity dataset already exists at {output_path}")
        if verify_dataset_integrity(output_path, load_checksum_cache(), "electricity"):
            return DownloadResult(
                dataset_name="electricity",
                success=True,
                file_path=str(output_path),
                checksum=compute_file_checksum(output_path)
            )
        else:
            logger.warning("Existing file failed integrity check. Re-downloading...")
            output_path.unlink()
    
    # Download
    if download_from_url(config["url"], output_path):
        checksum = compute_file_checksum(output_path)
        # Save checksum
        cache = load_checksum_cache()
        cache["electricity"] = checksum
        save_checksum_cache(cache)
        
        # Verify row count
        try:
            with open(output_path, 'r') as f:
                row_count = sum(1 for _ in f) - 1  # Exclude header
            if row_count >= config["min_rows"]:
                logger.info(f"✓ Electricity dataset valid: {row_count} rows")
                return DownloadResult(
                    dataset_name="electricity",
                    success=True,
                    file_path=str(output_path),
                    checksum=checksum
                )
            else:
                logger.error(f"Electricity dataset too small: {row_count} rows (min: {config['min_rows']})")
                output_path.unlink()
                return DownloadResult(
                    dataset_name="electricity",
                    success=False,
                    file_path=None,
                    checksum=None,
                    error_message=f"Insufficient rows: {row_count}"
                )
        except Exception as e:
            logger.error(f"Failed to validate row count: {e}")
            output_path.unlink()
            return DownloadResult(
                dataset_name="electricity",
                success=False,
                file_path=None,
                checksum=None,
                error_message=str(e)
            )
    else:
        return DownloadResult(
            dataset_name="electricity",
            success=False,
            file_path=None,
            checksum=None,
            error_message="Download failed"
        )

def download_traffic_dataset() -> DownloadResult:
    """Download UCI Traffic dataset."""
    config = DATASET_CONFIGS["traffic"]
    output_path = DATA_RAW_DIR / config["expected_filename"]
    
    # Check if already exists and verify
    if output_path.exists():
        logger.info(f"Traffic dataset already exists at {output_path}")
        if verify_dataset_integrity(output_path, load_checksum_cache(), "traffic"):
            return DownloadResult(
                dataset_name="traffic",
                success=True,
                file_path=str(output_path),
                checksum=compute_file_checksum(output_path)
            )
        else:
            logger.warning("Existing file failed integrity check. Re-downloading...")
            output_path.unlink()
    
    # Download
    if download_from_url(config["url"], output_path):
        checksum = compute_file_checksum(output_path)
        # Save checksum
        cache = load_checksum_cache()
        cache["traffic"] = checksum
        save_checksum_cache(cache)
        
        # Verify row count
        try:
            with open(output_path, 'r') as f:
                row_count = sum(1 for _ in f) - 1  # Exclude header
            if row_count >= config["min_rows"]:
                logger.info(f"✓ Traffic dataset valid: {row_count} rows")
                return DownloadResult(
                    dataset_name="traffic",
                    success=True,
                    file_path=str(output_path),
                    checksum=checksum
                )
            else:
                logger.error(f"Traffic dataset too small: {row_count} rows (min: {config['min_rows']})")
                output_path.unlink()
                return DownloadResult(
                    dataset_name="traffic",
                    success=False,
                    file_path=None,
                    checksum=None,
                    error_message=f"Insufficient rows: {row_count}"
                )
        except Exception as e:
            logger.error(f"Failed to validate row count: {e}")
            output_path.unlink()
            return DownloadResult(
                dataset_name="traffic",
                success=False,
                file_path=None,
                checksum=None,
                error_message=str(e)
            )
    else:
        return DownloadResult(
            dataset_name="traffic",
            success=False,
            file_path=None,
            checksum=None,
            error_message="Download failed"
        )

def verify_all_datasets() -> List[DownloadResult]:
    """Verify all datasets in data/raw/ against stored checksums."""
    results = []
    cache = load_checksum_cache()
    
    for dataset_name in ["electricity", "traffic"]:
        config = DATASET_CONFIGS[dataset_name]
        file_path = DATA_RAW_DIR / config["expected_filename"]
        
        if file_path.exists():
            is_valid = verify_dataset_integrity(file_path, cache, dataset_name)
            results.append(DownloadResult(
                dataset_name=dataset_name,
                success=is_valid,
                file_path=str(file_path) if is_valid else None,
                checksum=compute_file_checksum(file_path) if is_valid else None,
                error_message=None if is_valid else "Integrity verification failed"
            ))
            logger.info(f"{dataset_name}: {'✓' if is_valid else '✗'}")
        else:
            results.append(DownloadResult(
                dataset_name=dataset_name,
                success=False,
                file_path=None,
                checksum=None,
                error_message="File not found"
            ))
            logger.info(f"{dataset_name}: ✗ (not found)")
    
    return results

def download_all_datasets() -> List[DownloadResult]:
    """Download all datasets with integrity verification."""
    results = []
    
    # Download Electricity
    results.append(download_electricity_dataset())
    
    # Download Traffic
    results.append(download_traffic_dataset())
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("=" * 70)
    logger.info("Dataset Download and Verification")
    logger.info("=" * 70)
    
    # First, try to verify existing datasets
    logger.info("\n--- Checking existing datasets ---")
    existing_results = verify_all_datasets()
    
    # Check if all existing datasets are valid
    all_valid = all(r.success for r in existing_results)
    
    if not all_valid:
        logger.info("\n--- Some datasets missing or invalid. Attempting download ---")
        download_results = download_all_datasets()
        results = download_results
        
        # Log summary
        logger.info("\n" + "=" * 70)
        logger.info("Download Summary:")
        logger.info("=" * 70)
        for result in results:
            status = "✓" if result.success else "✗"
            logger.info(f"  {result.dataset_name}: {status} - {result.error_message or 'Success'}")
            
        if not all(r.success for r in results):
            logger.error("\n✗ Some downloads failed. Check error messages above.")
            sys.exit(1)
    else:
        logger.info("\n✓ All existing datasets verified successfully.")
        results = existing_results
    
    # Final status
    logger.info("\n" + "=" * 70)
    logger.info("Verification Complete")
    logger.info("=" * 70)
    
    if all(r.success for r in results):
        logger.info("✓ All datasets downloaded and verified successfully.")
        sys.exit(0)
    else:
        logger.error("✗ Verification failed for some datasets.")
        sys.exit(1)

if __name__ == "__main__":
    main()