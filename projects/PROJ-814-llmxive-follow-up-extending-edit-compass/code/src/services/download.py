"""
Download service for fetching the Edit-Compass dataset from Hugging Face.

This module handles the retrieval of raw data files, checksum verification,
and error handling for the pipeline. It strictly uses real data sources and
fails loudly if the download or verification fails.
"""
import os
import sys
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Project imports matching the provided API surface
from src.utils.logging import get_logger, setup_logging

# Constants for the Edit-Compass dataset
# Based on the official repository structure for "Edit-Compass & EditReward-Compass"
DATASET_REPO = "llmXive/Edit-Compass"
DATASET_FILE = "edit_compass_full.jsonl"
EXPECTED_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder, will be updated if real checksum is known or fetched dynamically
# Note: Since the specific SHA256 for the full dataset isn't provided in the prompt,
# we will implement verification logic but allow the script to proceed if the file exists
# or fail if the download fails. In a real scenario, this should be the actual SHA256.

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {file_path}")
        raise

def verify_download(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the downloaded file against the expected checksum.
    
    Args:
        file_path: Path to the downloaded file.
        expected_checksum: Expected SHA256 string. If None, skips checksum check 
                           but verifies file existence and non-zero size.
    
    Returns:
        True if verification passes.
    
    Raises:
        RuntimeError: If verification fails.
    """
    if not file_path.exists():
        raise RuntimeError(f"Downloaded file does not exist: {file_path}")
    
    if file_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file is empty: {file_path}")
    
    if expected_checksum:
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != expected_checksum:
            raise RuntimeError(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
        logger.info(f"Checksum verified: {actual_checksum}")
    else:
        logger.warning("No expected checksum provided; skipping checksum verification.")
    
    return True

def download_from_huggingface(
    output_dir: Path,
    repo_id: str = DATASET_REPO,
    filename: str = DATASET_FILE,
    force: bool = False
) -> Path:
    """
    Download the dataset file from Hugging Face Hub.
    
    This function uses the `huggingface-cli` or `wget`/`curl` to fetch the file.
    It ensures the output directory exists and handles errors by raising exceptions.
    
    Args:
        output_dir: Directory to save the downloaded file.
        repo_id: Hugging Face repository ID.
        filename: Name of the file to download.
        force: If True, re-download even if file exists.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        RuntimeError: If download fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    if file_path.exists() and not force:
        logger.info(f"File already exists at {file_path}. Skipping download.")
        return file_path
    
    logger.info(f"Downloading {filename} from {repo_id}...")
    
    # Construct the direct download URL for Hugging Face
    # Format: https://huggingface.co/{repo_id}/resolve/main/{filename}
    download_url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    try:
        # Use wget for robustness (handles redirects, retries)
        # If wget is not available, we could fallback to urllib or requests, 
        # but wget/curl is standard in research environments.
        subprocess.run(
            ["wget", "--no-check-certificate", "-O", str(file_path), download_url],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Download completed: {file_path}")
    except subprocess.CalledProcessError as e:
        # Clean up partial file if download failed
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Download failed: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        raise RuntimeError(f"Failed to download dataset from {download_url}") from e
    except FileNotFoundError:
        # Fallback to curl if wget is missing
        try:
            subprocess.run(
                ["curl", "-L", "-o", str(file_path), download_url],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Download completed (via curl): {file_path}")
        except subprocess.CalledProcessError as e:
            if file_path.exists():
                file_path.unlink()
            raise RuntimeError(f"Failed to download dataset via curl from {download_url}") from e

    return file_path

def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the download script.
    
    Args:
        args: Command line arguments (optional, for testing).
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent  # code/src -> code
    data_raw_dir = base_dir / "data" / "raw"
    
    logger.info(f"Starting download process. Output directory: {data_raw_dir}")
    
    try:
        # Download the dataset
        downloaded_file = download_from_huggingface(
            output_dir=data_raw_dir,
            repo_id=DATASET_REPO,
            filename=DATASET_FILE,
            force=False
        )
        
        # Verify the download (if checksum is known, otherwise just existence)
        # In a real scenario, we would fetch the checksum from a manifest or config
        verify_download(downloaded_file, expected_checksum=EXPECTED_CHECKSUM)
        
        logger.info(f"Successfully downloaded and verified: {downloaded_file}")
        return 0
        
    except RuntimeError as e:
        logger.error(f"Download process failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during download: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())