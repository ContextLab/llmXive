"""
Download USPTO dataset from canonical source 'flying-sausages/uspto_yield' using Hugging Face datasets.
Generates a SHA256 checksum immediately after fetch and logs it.
"""

import hashlib
import logging
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

# Ensure project root is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DATA_RAW_DIR, DATA_RESULTS_DIR

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_uspto_dataset(output_path: Path) -> Path:
    """
    Download USPTO dataset from 'flying-sausages/uspto_yield' on Hugging Face.
    
    The dataset is loaded, converted to Parquet, and saved to the specified output path.
    A SHA256 checksum is calculated and logged immediately after the file is written.
    The checksum is also written to data/results/download_checksum.txt.
    
    Args:
        output_path: Path where the parquet file will be saved.
        
    Returns:
        Path to the saved file.
        
    Raises:
        FileNotFoundError: If the dataset cannot be loaded or saved (fails loudly).
    """
    if output_path.exists():
        logger.warning(f"File already exists at {output_path}. Skipping download.")
        # Re-calculate checksum for existing file to ensure integrity
        actual_sha = calculate_sha256(output_path)
        logger.info(f"Existing file SHA256: {actual_sha}")
        _write_checksum(actual_sha)
        return output_path

    logger.info("Loading USPTO dataset from 'flying-sausages/uspto_yield'...")
    try:
        # Load the dataset. The 'uspto_yield' dataset typically has a 'train' split.
        # We load it into memory. The dataset is relatively small (approx 100k rows).
        dataset = load_dataset("flying-sausages/uspto_yield", split="train")
        
        logger.info(f"Dataset loaded successfully. Number of rows: {len(dataset)}")
        
        # Convert to Pandas DataFrame
        df = dataset.to_pandas()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving to {output_path}...")
        df.to_parquet(output_path, index=False)
        
        logger.info("File saved successfully.")
        
        # Calculate and log SHA256 checksum immediately
        checksum = calculate_sha256(output_path)
        logger.info(f"SHA256 checksum for {output_path}: {checksum}")
        
        # Write checksum to the specific results file
        _write_checksum(checksum)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        # Fail loudly as per requirements - do not fall back to synthetic
        raise FileNotFoundError(
            f"Failed to download USPTO dataset from 'flying-sausages/uspto_yield'. "
            f"Error: {e}"
        ) from e

def _write_checksum(checksum: str) -> None:
    """Write the checksum to the results directory."""
    checksum_path = DATA_RESULTS_DIR / "download_checksum.txt"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w") as f:
        f.write(checksum)
    logger.info(f"Checksum written to {checksum_path}")

def main():
    """Main entry point for download script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    output_path = DATA_RAW_DIR / "uspto_raw.parquet"
    
    try:
        download_uspto_dataset(output_path)
        logger.info("Dataset download and verification complete.")
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        raise

if __name__ == "__main__":
    main()