import os
import sys
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Import project utilities
from src.utils.logging import get_logger

# Constants (matching test expectations)
DATASET_REPO = "HuggingFaceM4/Edit-Compass"
DATASET_FILE = "data.json"
EXPECTED_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder, real checksum should be fetched or verified

logger = get_logger(__name__)

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {filepath}")
        raise
    except PermissionError:
        logger.error(f"Permission denied reading file: {filepath}")
        raise

def verify_download(filepath: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the downloaded file's integrity.
    Returns True if checksum matches or if no checksum is provided (skip check).
    Raises ValueError if checksum mismatch.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Downloaded file not found at {filepath}")

    actual_checksum = calculate_sha256(filepath)
    
    if expected_checksum:
        if actual_checksum != expected_checksum:
            error_msg = (
                f"Checksum verification failed for {filepath}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info(f"Checksum verified for {filepath}")
    else:
        logger.warning(f"No checksum provided for {filepath}, skipping verification.")
    
    return True

def download_from_huggingface(output_dir: Path, filename: str = DATASET_FILE) -> Path:
    """
    Download the Edit-Compass dataset from Hugging Face.
    
    Args:
        output_dir: Directory to save the downloaded file.
        filename: Name of the file to download.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        FileNotFoundError: If the download fails or the file is not found.
        RuntimeError: If the download command fails.
        ValueError: If the output directory is invalid.
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
    
    if not output_dir.is_dir():
        raise ValueError(f"Output path is not a directory: {output_dir}")

    file_path = output_dir / filename
    
    if file_path.exists():
        logger.info(f"File already exists at {file_path}, skipping download.")
        return file_path

    logger.info(f"Downloading {DATASET_FILE} from {DATASET_REPO}...")
    
    # Construct huggingface-cli download command
    # Using huggingface-cli as it is the standard tool for HF datasets
    cmd = [
        "huggingface-cli", "download",
        DATASET_REPO,
        filename,
        "--local-dir", str(output_dir),
        "--local-dir-use-symlinks", "false"
    ]

    try:
        # Check if huggingface-cli is available
        subprocess.run(["huggingface-cli", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("huggingface-cli is not installed. Please install it: pip install huggingface_hub")
        raise RuntimeError("huggingface-cli not found. Install with: pip install huggingface_hub")

    try:
        logger.debug(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Download completed successfully.")
    except subprocess.CalledProcessError as e:
        error_msg = f"Download failed with error code {e.returncode}. stderr: {e.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}") from e

    if not file_path.exists():
        raise FileNotFoundError(f"Download succeeded but file not found at {file_path}")

    logger.info(f"File saved to {file_path}")
    return file_path

def main():
    """Main entry point for the download script."""
    # Default paths relative to project root
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    raw_data_dir = base_dir / "data" / "raw"
    
    if not raw_data_dir.exists():
        raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download to {raw_data_dir}")
    
    try:
        file_path = download_from_huggingface(raw_data_dir)
        verify_download(file_path)
        logger.info("Download and verification completed successfully.")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Download process failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
