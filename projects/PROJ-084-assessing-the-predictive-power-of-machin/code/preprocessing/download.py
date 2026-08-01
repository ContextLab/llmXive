"""
Download USPTO dataset from canonical source and verify checksum.
"""

import os
import hashlib
import logging
from pathlib import Path

# Note: This is a placeholder for the actual download logic.
# The real implementation would fetch from the DOI source specified in the spec.
# For now, it assumes the data exists or fails loudly.

logger = logging.getLogger(__name__)

def calculate_md5(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate MD5 checksum of a file."""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def download_uspto_dataset(output_path: Path, expected_md5: str) -> Path:
    """
    Download USPTO dataset from canonical source.

    This function should be implemented to fetch the dataset from the
    DOI source specified in the project specification. For now, it
    raises an error if the file does not exist, enforcing the
    "fail loudly" requirement.
    """
    if output_path.exists():
        logger.info(f"File already exists: {output_path}")
        # Verify checksum if expected_md5 is provided
        if expected_md5:
            actual_md5 = calculate_md5(output_path)
            if actual_md5 != expected_md5:
                raise ValueError(f"Checksum mismatch: expected {expected_md5}, got {actual_md5}")
        return output_path

    # TODO: Implement actual download from DOI source
    # For now, fail loudly as per requirements
    raise FileNotFoundError(
        f"USPTO dataset not found at {output_path}. "
        "Please download from the canonical source (DOI) and place it here. "
        "This is a strict requirement to ensure verified accuracy."
    )

def main():
    """Main entry point for download script."""
    logging.basicConfig(level=logging.INFO)

    # Define paths (adjust based on project structure)
    output_path = Path("data/raw/uspto_raw.parquet")
    expected_md5 = ""  # TODO: Set expected MD5 from manifest

    try:
        download_uspto_dataset(output_path, expected_md5)
        logger.info("Dataset download/verification complete.")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

if __name__ == "__main__":
    main()
