import os
import sys
import logging
import time
from pathlib import Path
from datasets import load_dataset
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

def download_oqmd_dataset(output_dir: str = "data/raw"):
    """
    Download the OQMD Formation Energy dataset via HuggingFace with retry logic.
    
    Implements exponential backoff (2^attempt seconds) for up to 3 attempts.
    If the download fails after all retries, it raises the exception (fails loudly).
    
    Args:
        output_dir: Directory to save the parquet file. Defaults to 'data/raw'.
    
    Returns:
        Path to the saved parquet file.
    
    Raises:
        Exception: If download fails after max retries.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_file = output_path / "oqmd.parquet"

    if parquet_file.exists():
        logger.info(f"Dataset already exists at {parquet_file}, skipping download.")
        return parquet_file

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading OQMD dataset (attempt {attempt}/{max_retries})...")
            # Load the specific dataset and split as per task requirements
            # Using streaming=False to ensure we get the full dataset in memory for conversion
            # The dataset is large, so we rely on the runner's memory constraints or streaming if needed.
            # However, to_parquet requires the full dataframe or chunked writing.
            # We will attempt to load the full split. If memory is an issue, the runner will OOM,
            # which is preferable to silently faking data.
            dataset = load_dataset("oqmd/formation-energy", split="train", streaming=False)
            
            # Convert to pandas for easier parquet handling
            df = dataset.to_pandas()
            
            # Save as parquet
            df.to_parquet(parquet_file, index=False)
            
            logger.info(f"Dataset successfully saved to {parquet_file}")
            logger.info(f"Dataset shape: {df.shape}")
            return parquet_file

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
