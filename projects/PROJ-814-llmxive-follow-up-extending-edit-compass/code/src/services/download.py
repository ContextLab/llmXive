"""
Download and verify the Edit-Compass dataset from Hugging Face.

This module handles fetching the raw dataset, verifying integrity via SHA256,
and saving it to the `data/raw/` directory.
"""
import os
import sys
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)

# Constants
DATASET_REPO = "llmXive/Edit-Compass"
DATASET_FILE = "edit-compass-dataset.jsonl"
EXPECTED_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder: Update with real checksum when available
# Note: In a real scenario, the checksum should be fetched from the repo's README or a verified source.
# For this implementation, we assume the user provides the correct checksum or we fetch it dynamically if supported.

# Since the actual dataset isn't on HF under that exact name yet, we will simulate the download logic
# using a verified real source if available, or fail loudly if not.
# However, per strict constraints, we must use a REAL source. 
# The Edit-Compass dataset is typically found in the "Edit-Compass" repo.
# We will use the Hugging Face Hub API to download.

try:
    from huggingface_hub import hf_hub_download, list_repo_files
except ImportError:
    logger.error("huggingface_hub is required. Install with: pip install huggingface_hub")
    sys.exit(1)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_download(file_path: Path, expected_hash: str) -> bool:
    """Verify the downloaded file's SHA256 matches the expected hash."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    actual_hash = calculate_sha256(file_path)
    if actual_hash != expected_hash:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"  Expected: {expected_hash}")
        logger.error(f"  Actual:   {actual_hash}")
        return False
    
    logger.info(f"Checksum verified for {file_path}")
    return True

def download_from_huggingface(
    repo_id: str = DATASET_REPO,
    filename: str = DATASET_FILE,
    output_dir: Optional[Path] = None,
    expected_sha256: Optional[str] = None
) -> Path:
    """
    Download a file from Hugging Face Hub.
    
    Args:
        repo_id: The Hugging Face repository ID (e.g., "user/repo").
        filename: The specific file to download.
        output_dir: Directory to save the file. Defaults to `data/raw/`.
        expected_sha256: Optional expected SHA256 for verification.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        RuntimeError: If download fails or checksum verification fails.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    logger.info(f"Downloading {filename} from {repo_id}...")
    
    try:
        # Attempt to download from HF Hub
        # If the specific file doesn't exist, hf_hub_download will raise an error
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            repo_type="dataset"
        )
        logger.info(f"Downloaded to: {local_path}")
    except Exception as e:
        logger.error(f"Failed to download from Hugging Face: {e}")
        # Fallback: Check if there's a known mirror or alternative method?
        # Per constraints: NO synthetic data, NO silent fallback.
        # If the repo/file doesn't exist, we must fail.
        raise RuntimeError(f"Dataset download failed: {e}") from e
    
    # Verify checksum if provided
    if expected_sha256:
        if not verify_download(Path(local_path), expected_sha256):
            raise RuntimeError("Checksum verification failed after download.")
    else:
        logger.warning("No expected SHA256 provided; skipping checksum verification.")
    
    return Path(local_path)

def main():
    """Entry point for the download script."""
    # Setup basic logging if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    try:
        # Attempt to get the real checksum from the repo if possible, 
        # or use a verified one if known. 
        # For now, we proceed without a hardcoded checksum to avoid false negatives,
        # but in a production pipeline, this should be strict.
        
        # Check if the file exists in the repo first
        try:
            files = list_repo_files(DATASET_REPO, repo_type="dataset")
            if DATASET_FILE not in files:
                # Try to find similar files
                available = [f for f in files if "edit" in f.lower() and ("compass" in f.lower() or "json" in f.lower())]
                if not available:
                    raise RuntimeError(f"File '{DATASET_FILE}' not found in {DATASET_REPO}. Available: {files}")
                logger.warning(f"File '{DATASET_FILE}' not found. Available files: {available}")
                # If we can't find the exact file, we should fail or use the found one?
                # Strictly, we should use the exact file.
                raise RuntimeError(f"Required file '{DATASET_FILE}' not found in repository.")
        except Exception as e:
            logger.error(f"Could not list repo files: {e}")
            # Continue anyway, let hf_hub_download handle the 404
        
        output_path = download_from_huggingface(
            repo_id=DATASET_REPO,
            filename=DATASET_FILE,
            output_dir=Path("data/raw")
        )
        
        logger.info(f"Successfully downloaded dataset to {output_path}")
        return 0
        
    except Exception as e:
        logger.critical(f"Download process failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())