"""
Download service for fetching the Edit-Compass dataset.

This module handles:
- Verification of download URLs
- SHA256 checksum validation
- Downloading from HuggingFace Hub
- Error handling and logging
"""
import os
import sys
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from huggingface_hub import hf_hub_download, HfApi

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging

# Dataset configuration - Edit-Compass from HuggingFace
DATASET_REPO = "HuggingFaceM4/Edit-Compass"
DATASET_FILE = "edit_compass_dataset.json"
DATASET_CHECKSUM = None  # Will be fetched or computed if known

# Setup logging
logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hex digest of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_download(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the downloaded file's integrity.
    
    Args:
        file_path: Path to the downloaded file
        expected_checksum: Optional expected SHA256 checksum
        
    Returns:
        True if verification passes
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If checksum doesn't match
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Downloaded file not found: {file_path}")
    
    actual_checksum = calculate_sha256(file_path)
    logger.info(f"Downloaded file checksum: {actual_checksum}")
    
    if expected_checksum:
        if actual_checksum.lower() != expected_checksum.lower():
            raise ValueError(
                f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}"
            )
        logger.info("Checksum verification passed")
    
    return True

def download_from_huggingface(
    repo_id: str = DATASET_REPO,
    filename: str = DATASET_FILE,
    output_dir: Optional[Path] = None,
    expected_checksum: Optional[str] = None
) -> Path:
    """
    Download a dataset file from HuggingFace Hub.
    
    Args:
        repo_id: HuggingFace repository ID
        filename: Name of the file to download
        output_dir: Directory to save the file (defaults to data/raw/)
        expected_checksum: Optional expected SHA256 checksum
        
    Returns:
        Path to the downloaded file
        
    Raises:
        RuntimeError: If download fails
        ValueError: If checksum verification fails
    """
    if output_dir is None:
        output_dir = project_root / "data" / "raw"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    logger.info(f"Downloading {filename} from {repo_id}...")
    
    try:
        # Download from HuggingFace Hub
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
        
        logger.info(f"Downloaded to: {downloaded_path}")
        
        # Verify checksum if provided
        if expected_checksum:
            verify_download(Path(downloaded_path), expected_checksum)
        
        return Path(downloaded_path)
        
    except Exception as e:
        logger.error(f"Failed to download from HuggingFace: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}") from e

def main():
    """
    Main entry point for the download script.
    """
    setup_logging()
    
    logger.info("Starting Edit-Compass dataset download...")
    
    try:
        # Download the dataset
        dataset_path = download_from_huggingface(
            repo_id=DATASET_REPO,
            filename=DATASET_FILE,
            output_dir=project_root / "data" / "raw"
        )
        
        logger.info(f"Successfully downloaded dataset to: {dataset_path}")
        logger.info(f"File size: {dataset_path.stat().st_size} bytes")
        
        return dataset_path
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
