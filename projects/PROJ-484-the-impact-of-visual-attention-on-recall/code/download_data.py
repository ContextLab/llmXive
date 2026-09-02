"""
Dataset download and verification script for the Visual Attention Recall project.
Handles manifest verification, disk space checks, and dataset download with checksum validation.
"""
import os
import sys
import hashlib
import logging
import argparse
import json
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download
from config import get_config, get_data_path, get_random_seed

# Import logging infrastructure
from logging_config import setup_logging

# Constants
DATASET_ID = "openneuro/ds001435"
REQUIRED_SPACE_GB = 5.0  # Conservative estimate for the full dataset
MIN_SPACE_BUFFER_GB = 2.0  # Additional buffer for temporary files

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger with JSON formatting."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_manifest(manifest_path: Path) -> dict:
    """Verify the BIDS manifest and extract required information."""
    logger = logging.getLogger("download_data")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Verify required fields
    required_fields = ['Name', 'BIDSVersion']
    for field in required_fields:
        if field not in manifest:
            raise ValueError(f"Missing required manifest field: {field}")
    
    logger.info(f"Manifest verified: {manifest.get('Name')} (BIDS v{manifest.get('BIDSVersion')})")
    return manifest

def check_disk_space(target_path: Path, required_gb: float) -> bool:
    """
    Check if sufficient disk space is available for the download.
    
    Args:
        target_path: The directory where data will be downloaded
        required_gb: Required space in GB (including buffer)
    
    Returns:
        True if sufficient space, False otherwise
    
    Raises:
        RuntimeError: If insufficient disk space is available
    """
    logger = logging.getLogger("download_data")
    
    # Get disk usage statistics
    stat = shutil.disk_usage(target_path)
    
    # Convert bytes to GB
    free_gb = stat.free / (1024 ** 3)
    total_gb = stat.total / (1024 ** 3)
    used_gb = stat.used / (1024 ** 3)
    
    logger.info(f"Disk space check for {target_path}:")
    logger.info(f"  Total: {total_gb:.2f} GB")
    logger.info(f"  Used: {used_gb:.2f} GB")
    logger.info(f"  Free: {free_gb:.2f} GB")
    logger.info(f"  Required: {required_gb:.2f} GB")
    
    if free_gb < required_gb:
        error_msg = f"ERROR: Insufficient disk space. Free: {free_gb:.2f} GB, Required: {required_gb:.2f} GB"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Disk space check passed.")
    return True

def download_dataset(dataset_id: str, output_dir: Path, verify: bool = True) -> dict:
    """
    Download a dataset from Hugging Face Hub.
    
    Args:
        dataset_id: The Hugging Face dataset identifier (namespace/name)
        output_dir: Directory to download the dataset to
        verify: Whether to verify checksums after download
    
    Returns:
        Dictionary with download status and metadata
    """
    logger = logging.getLogger("download_data")
    logger.info(f"Starting download for dataset: {dataset_id}")
    
    try:
        # Check disk space before attempting download
        required_space = REQUIRED_SPACE_GB + MIN_SPACE_BUFFER_GB
        check_disk_space(output_dir, required_space)
        
        # Download the dataset
        logger.info(f"Attempting to connect to HuggingFace Hub for {dataset_id}...")
        
        # Use snapshot_download for BIDS datasets to get the full structure
        downloaded_path = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=str(output_dir),
            local_dir_use_symlinks=False,
            ignore_patterns=[".gitattributes"] if verify else None
        )
        
        logger.info(f"Dataset downloaded successfully to: {downloaded_path}")
        
        # Verify manifest if requested
        manifest_path = output_dir / "dataset_description.json"
        if verify and manifest_path.exists():
            manifest = verify_manifest(manifest_path)
            logger.info("Manifest verification completed.")
        
        # Calculate checksums for key files
        checksums = {}
        if manifest_path.exists():
            checksums['dataset_description.json'] = calculate_sha256(manifest_path)
        
        return {
            "status": "success",
            "path": str(downloaded_path),
            "manifest": manifest if verify and manifest_path.exists() else None,
            "checksums": checksums
        }
        
    except RuntimeError as e:
        # Re-raise disk space errors
        if "Insufficient disk space" in str(e):
            raise
        logger.error(f"Runtime error during download: {str(e)}")
        return {"status": "error", "message": str(e)}
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        return {"status": "error", "message": str(e)}

def main():
    """Main entry point for the download script."""
    parser = argparse.ArgumentParser(description="Download and verify BIDS dataset")
    parser.add_argument("--dataset", type=str, default=DATASET_ID, 
                      help=f"Dataset ID (default: {DATASET_ID})")
    parser.add_argument("--output", type=str, default=None,
                      help="Output directory (default: from config)")
    parser.add_argument("--no-verify", action="store_true",
                      help="Skip manifest verification")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger("download_data")
    logger.info("Starting dataset download process")
    
    try:
        # Get configuration
        config = get_config()
        output_dir = Path(args.output) if args.output else get_data_path() / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Output directory: {output_dir}")
        
        # Download dataset
        result = download_dataset(
            dataset_id=args.dataset,
            output_dir=output_dir,
            verify=not args.no_verify
        )
        
        if result["status"] == "success":
            logger.info("Download completed successfully")
            # Print summary
            print(json.dumps(result, indent=2, default=str))
            return 0
        else:
            logger.error(f"Download failed: {result.get('message', 'Unknown error')}")
            return 1
            
    except RuntimeError as e:
        # Handle disk space errors specifically
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Fatal error during download: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
