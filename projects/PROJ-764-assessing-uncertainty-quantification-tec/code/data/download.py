import os
import sys
import logging
import time
import json
import hashlib
from pathlib import Path
from datasets import load_dataset

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_oqmd_dataset(output_dir: str = "data/raw", checksum_dir: str = "data"):
    """
    Download the OQMD Formation Energy dataset via HuggingFace with retry logic.
    
    Implements exponential backoff (2^attempt seconds) for up to 3 attempts.
    If the download fails after all retries, it raises the exception (fails loudly).
    Materializes the dataset to a parquet file and calculates a SHA-256 checksum.
    
    Args:
        output_dir: Directory to save the parquet file. Defaults to 'data/raw'.
        checksum_dir: Directory to save the checksums.json file. Defaults to 'data'.
    
    Returns:
        Path to the saved parquet file.
    
    Raises:
        Exception: If download fails after max retries.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_file = output_path / "oqmd.parquet"
    
    checksum_path = Path(checksum_dir) / "checksums.json"

    if parquet_file.exists():
        logger.info(f"Dataset already exists at {parquet_file}, skipping download.")
    else:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Downloading OQMD dataset (attempt {attempt}/{max_retries})...")
                # Load the specific dataset and split as per task requirements
                # Using streaming=False to ensure we get the full dataset for conversion
                # The dataset is large; if memory is an issue, the runner will OOM,
                # which is preferable to silently faking data.
                dataset = load_dataset("oqmd/formation-energy", split="train", streaming=False)
                
                # Convert to pandas for easier parquet handling
                df = dataset.to_pandas()
                
                # Save as parquet
                df.to_parquet(parquet_file, index=False)
                
                logger.info(f"Dataset successfully saved to {parquet_file}")
                logger.info(f"Dataset shape: {df.shape}")
                break

            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {type(e).__name__}: {e}")
                if attempt < max_retries:
                    # Exponential backoff: 2^1=2s, 2^2=4s
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Failed to download dataset after all retry attempts.")
                    raise

    # Calculate checksum
    logger.info(f"Calculating SHA-256 checksum for {parquet_file}...")
    sha256_hash = calculate_sha256(parquet_file)
    logger.info(f"SHA-256: {sha256_hash}")

    # Record checksum
    checksum_data = {
        "filename": "oqmd.parquet",
        "sha256": sha256_hash
    }
    
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    
    logger.info(f"Checksum recorded in {checksum_path}")

    return parquet_file

def main():
    """Entry point for the download script."""
    # Configure logging to stdout
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting OQMD dataset download...")
    try:
        output_file = download_oqmd_dataset()
        logger.info(f"Download complete. Output: {output_file}")
    except Exception as e:
        logger.critical(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
