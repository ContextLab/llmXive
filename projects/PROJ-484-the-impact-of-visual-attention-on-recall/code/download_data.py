"""
Dataset download script for the Visual Attention on Recall project.

Downloads the RSVP dataset from HuggingFace Hub with checksum verification.
Does NOT implement synthetic fallbacks; fails loudly if fetch fails.
"""
import os
import sys
import hashlib
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logging_config import setup_logging

# Configure logging
logger = setup_logging("download_data")

# Configuration
DATASET_REPO = "visual_attention_rsvp_dataset"  # Placeholder ID; will be replaced if a real source is provided
# NOTE: In a real implementation, this would be a verified HuggingFace dataset ID or a specific URL.
# Since no real source was provided in the context, we use a generic structure that expects a real dataset.
# If the dataset does not exist, this will raise an error as required.

# Expected checksums (to be populated when the real dataset is identified)
# For now, we rely on HuggingFace's internal integrity checks.
EXPECTED_CHECKSUMS = {} 

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(output_dir: str) -> None:
    """
    Download the dataset from HuggingFace Hub.
    
    Args:
        output_dir: Directory where the dataset will be saved.
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or downloaded.
        RuntimeError: If checksum verification fails.
    """
    try:
        from datasets import load_dataset
        from huggingface_hub import snapshot_download
    except ImportError as e:
        logger.error(f"Required library missing: {e}. Please install datasets and huggingface_hub.")
        raise

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Attempting to download dataset '{DATASET_REPO}' to {output_path}")

    try:
        # Attempt to download the dataset snapshot
        # Using snapshot_download to get the raw files
        downloaded_path = snapshot_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            local_dir=str(output_path),
            local_dir_use_symlinks=False
        )
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise FileNotFoundError(f"Dataset '{DATASET_REPO}' not found or inaccessible: {e}")

    # Verify checksums if defined
    if EXPECTED_CHECKSUMS:
        logger.info("Verifying checksums...")
        for filename, expected_hash in EXPECTED_CHECKSUMS.items():
            file_path = output_path / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Expected file '{filename}' not found after download.")
            
            actual_hash = calculate_sha256(str(file_path))
            if actual_hash != expected_hash:
                raise RuntimeError(
                    f"Checksum mismatch for '{filename}': "
                    f"expected {expected_hash}, got {actual_hash}"
                )
        logger.info("Checksum verification passed.")
    else:
        logger.warning("No checksums defined for verification. Skipping integrity check.")

    logger.info(f"Dataset successfully downloaded to {output_path}")

def main():
    """Main entry point."""
    # Determine output directory based on project structure
    # Assuming script is in code/ and output goes to data/raw/
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "data" / "raw"

    logger.info(f"Starting dataset download. Output directory: {output_dir}")
    
    try:
        download_dataset(str(output_dir))
        logger.info("Dataset download completed successfully.")
    except (FileNotFoundError, RuntimeError) as e:
        logger.error(f"Dataset download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()