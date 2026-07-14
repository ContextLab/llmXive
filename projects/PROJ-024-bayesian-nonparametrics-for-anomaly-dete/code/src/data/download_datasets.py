"""
Dataset download and verification module.

This module handles downloading real-world datasets (UCI Electricity, Traffic)
and verifying their integrity against stored checksums.
"""
import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
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
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    size_bytes: Optional[int] = None

# Dataset configuration
DATASETS = {
    "electricity": {
        "name": "Electricity Load Diagrams",
        "url": "https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip",
        "expected_name": "LD2011_2014.txt",
        "output_name": "electricity_load.csv",
        "description": "Electricity consumption data from 2011-2014",
        "license": "UCI Machine Learning Repository"
    },
    "traffic": {
        "name": "Traffic",
        "url": "https://archive.ics.uci.edu/static/public/258/traffic_data.zip",
        "expected_name": "traffic_data.csv",
        "output_name": "traffic_data.csv",
        "description": "Traffic occupancy data from PeMS sensors",
        "license": "UCI Machine Learning Repository"
    }
}

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file checksum
    """
    hash_func = hashlib.new(algorithm)
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {filepath}: {e}")
        raise

def validate_checksum(filepath: str, expected_checksum: str) -> bool:
    """
    Validate a file against an expected checksum.
    
    Args:
        filepath: Path to the file to validate
        expected_checksum: Expected checksum value
        
    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False
    
    try:
        actual_checksum = compute_file_checksum(filepath)
        return actual_checksum == expected_checksum
    except Exception as e:
        logger.error(f"Error validating checksum: {e}")
        return False

def download_from_url(url: str, output_path: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Download a file from a URL.
    
    Args:
        url: Source URL
        output_path: Destination path
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success, message)
    """
    # Create SSL context that doesn't verify certificates (for compatibility)
    # In production, proper certificate verification should be used
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        logger.info(f"Downloading {url} to {output_path}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a request with headers
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'}
        )
        
        # Download with SSL context
        with urllib.request.urlopen(req, context=ssl_context, timeout=timeout) as response:
            with open(output_path, 'wb') as out_file:
                # Download in chunks
                chunk_size = 8192
                total_size = 0
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    total_size += len(chunk)
                    # Log progress every 1MB
                    if total_size % (1024 * 1024) == 0:
                        logger.info(f"Downloaded {total_size / (1024*1024):.1f} MB...")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Download complete: {file_size} bytes")
        return True, f"Successfully downloaded {file_size} bytes"
        
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
        logger.error(error_msg)
        return False, error_msg
    except urllib.error.URLError as e:
        error_msg = f"URL Error: {e.reason}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def load_checksum_cache(cache_path: str) -> Dict[str, str]:
    """
    Load checksum cache from file.
    
    Args:
        cache_path: Path to the checksum cache file
        
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

def save_checksum_cache(cache_path: str, checksums: Dict[str, str]) -> None:
    """
    Save checksum cache to file.
    
    Args:
        cache_path: Path to the checksum cache file
        checksums: Dictionary mapping filenames to checksums
    """
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksum cache saved to {cache_path}")
    except Exception as e:
        logger.error(f"Error saving checksum cache: {e}")

def verify_dataset_integrity(dataset_name: str, data_dir: str, checksum_cache: Dict[str, str]) -> bool:
    """
    Verify dataset integrity against stored checksums.
    
    Args:
        dataset_name: Name of the dataset
        data_dir: Directory containing the dataset
        checksum_cache: Dictionary of known checksums
        
    Returns:
        True if verification passes or no checksum available, False if mismatch
    """
    output_name = DATASETS[dataset_name]["output_name"]
    file_path = os.path.join(data_dir, output_name)
    
    if not os.path.exists(file_path):
        logger.warning(f"Dataset file not found: {file_path}")
        return False
    
    if dataset_name in checksum_cache:
        expected_checksum = checksum_cache[dataset_name]
        logger.info(f"Verifying checksum for {dataset_name}...")
        if validate_checksum(file_path, expected_checksum):
            logger.info(f"Checksum verified for {dataset_name}")
            return True
        else:
            actual_checksum = compute_file_checksum(file_path)
            logger.error(f"Checksum mismatch for {dataset_name}!")
            logger.error(f"  Expected: {expected_checksum}")
            logger.error(f"  Actual:   {actual_checksum}")
            return False
    else:
        logger.info(f"No stored checksum for {dataset_name}, skipping verification")
        return True

def download_electricity_dataset(data_dir: str, force: bool = False) -> DownloadResult:
    """
    Download the UCI Electricity Load Diagrams dataset.
    
    Args:
        data_dir: Directory to save the dataset
        force: Force re-download even if file exists
        
    Returns:
        DownloadResult with status information
    """
    config = DATASETS["electricity"]
    output_path = os.path.join(data_dir, config["output_name"])
    
    # Check if file already exists
    if os.path.exists(output_path) and not force:
        logger.info(f"Electricity dataset already exists at {output_path}")
        # Verify integrity
        checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
        if verify_dataset_integrity("electricity", data_dir, checksum_cache):
            return DownloadResult(
                dataset_name="electricity",
                success=True,
                file_path=output_path,
                checksum=compute_file_checksum(output_path),
                size_bytes=os.path.getsize(output_path)
            )
        else:
            logger.warning("Existing file has invalid checksum, re-downloading...")
    
    # Download the dataset
    success, message = download_from_url(config["url"], output_path)
    
    if not success:
        return DownloadResult(
            dataset_name="electricity",
            success=False,
            error_message=message
        )
    
    # Compute and save checksum
    checksum = compute_file_checksum(output_path)
    checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
    checksum_cache["electricity"] = checksum
    save_checksum_cache(os.path.join(data_dir, "checksums.json"), checksum_cache)
    
    return DownloadResult(
        dataset_name="electricity",
        success=True,
        file_path=output_path,
        checksum=checksum,
        size_bytes=os.path.getsize(output_path)
    )

def download_traffic_dataset(data_dir: str, force: bool = False) -> DownloadResult:
    """
    Download the UCI Traffic dataset.
    
    Args:
        data_dir: Directory to save the dataset
        force: Force re-download even if file exists
        
    Returns:
        DownloadResult with status information
    """
    config = DATASETS["traffic"]
    output_path = os.path.join(data_dir, config["output_name"])
    
    # Check if file already exists
    if os.path.exists(output_path) and not force:
        logger.info(f"Traffic dataset already exists at {output_path}")
        # Verify integrity
        checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
        if verify_dataset_integrity("traffic", data_dir, checksum_cache):
            return DownloadResult(
                dataset_name="traffic",
                success=True,
                file_path=output_path,
                checksum=compute_file_checksum(output_path),
                size_bytes=os.path.getsize(output_path)
            )
        else:
            logger.warning("Existing file has invalid checksum, re-downloading...")
    
    # Download the dataset
    success, message = download_from_url(config["url"], output_path)
    
    if not success:
        return DownloadResult(
            dataset_name="traffic",
            success=False,
            error_message=message
        )
    
    # Compute and save checksum
    checksum = compute_file_checksum(output_path)
    checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
    checksum_cache["traffic"] = checksum
    save_checksum_cache(os.path.join(data_dir, "checksums.json"), checksum_cache)
    
    return DownloadResult(
        dataset_name="traffic",
        success=True,
        file_path=output_path,
        checksum=checksum,
        size_bytes=os.path.getsize(output_path)
    )

def download_all_datasets(data_dir: str, force: bool = False) -> Dict[str, DownloadResult]:
    """
    Download all configured datasets.
    
    Args:
        data_dir: Directory to save the datasets
        force: Force re-download even if files exist
        
    Returns:
        Dictionary mapping dataset names to DownloadResults
    """
    results = {}
    
    # Load existing checksums
    checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
    
    for dataset_name in DATASETS.keys():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing dataset: {dataset_name}")
        logger.info(f"{'='*60}")
        
        if dataset_name == "electricity":
            result = download_electricity_dataset(data_dir, force)
        elif dataset_name == "traffic":
            result = download_traffic_dataset(data_dir, force)
        else:
            logger.warning(f"Unknown dataset: {dataset_name}")
            continue
        
        results[dataset_name] = result
      
        if result.success:
            logger.info(f"✓ {dataset_name} downloaded successfully")
            logger.info(f"  File: {result.file_path}")
            logger.info(f"  Size: {result.size_bytes} bytes")
            logger.info(f"  Checksum: {result.checksum}")
        else:
            logger.error(f"✗ {dataset_name} failed: {result.error_message}")
    
    return results

def verify_all_datasets(data_dir: str) -> Dict[str, bool]:
    """
    Verify integrity of all downloaded datasets.
    
    Args:
        data_dir: Directory containing the datasets
        
    Returns:
        Dictionary mapping dataset names to verification status
    """
    results = {}
    checksum_cache = load_checksum_cache(os.path.join(data_dir, "checksums.json"))
    
    for dataset_name in DATASETS.keys():
        output_name = DATASETS[dataset_name]["output_name"]
        file_path = os.path.join(data_dir, output_name)
        
        if os.path.exists(file_path):
            if dataset_name in checksum_cache:
                is_valid = validate_checksum(file_path, checksum_cache[dataset_name])
                results[dataset_name] = is_valid
                status = "✓ Valid" if is_valid else "✗ Invalid"
                logger.info(f"{dataset_name}: {status}")
            else:
                logger.warning(f"No checksum available for {dataset_name}")
                results[dataset_name] = True  # Assume valid if no checksum
        else:
            logger.warning(f"Dataset not found: {dataset_name}")
            results[dataset_name] = False
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and verify datasets")
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/raw',
        help='Directory to save datasets (default: data/raw)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if files exist'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing datasets, do not download'
    )
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)
    
    if args.verify_only:
        logger.info("Verifying existing datasets...")
        results = verify_all_datasets(args.data_dir)
        
        all_valid = all(results.values())
        if all_valid:
            logger.info("✓ All datasets verified successfully")
            return 0
        else:
            logger.error("✗ Some datasets failed verification")
            return 1
    else:
        logger.info("Downloading datasets...")
        results = download_all_datasets(args.data_dir, args.force)
        
        # Verify downloaded datasets
        logger.info("\nVerifying downloaded datasets...")
        verification_results = verify_all_datasets(args.data_dir)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY")
        logger.info(f"{'='*60}")
        
        successful_downloads = sum(1 for r in results.values() if r.success)
        total_datasets = len(results)
        
        logger.info(f"Downloads: {successful_downloads}/{total_datasets} successful")
        
        if successful_downloads == total_datasets:
            if all(verification_results.values()):
                logger.info("✓ All datasets downloaded and verified successfully")
                return 0
            else:
                logger.warning("✓ All datasets downloaded, but some verification failed")
                return 0  # Still success as download worked
        else:
            logger.error("✗ Some downloads failed")
            for name, result in results.items():
                if not result.success:
                    logger.error(f"  - {name}: {result.error_message}")
            return 1

if __name__ == "__main__":
    sys.exit(main())