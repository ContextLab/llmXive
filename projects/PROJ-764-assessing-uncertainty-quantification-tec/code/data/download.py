"""
Download the OQMD Formation Energy dataset from HuggingFace.

This script fetches the 'oqmd/formation-energy' dataset and saves it
as a Parquet file in the data/raw directory.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def download_oqmd_dataset():
    """
    Fetches the OQMD Formation Energy dataset via HuggingFace and saves it to disk.
    
    Raises:
        ImportError: If the 'datasets' library is not installed.
        Exception: If the download fails.
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        logger.error("The 'datasets' library is required. Install it via: pip install datasets")
        raise e

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "oqmd.parquet"

    logger.info(f"Starting download of 'oqmd/formation-energy' dataset...")
    logger.info(f"Target path: {output_path}")

    try:
        # Load the dataset from HuggingFace
        dataset = load_dataset("oqmd/formation-energy")
        
        # The dataset usually comes as a Dict[str, Dataset]. 
        # We assume the first split (often 'train' or the only split) is the target.
        # If the dataset has multiple splits, we concatenate them or pick the main one.
        # Based on typical OQMD HF datasets, it often has a 'train' split.
        
        splits = list(dataset.keys())
        if not splits:
            raise ValueError("The loaded dataset has no splits.")
        
        # If there are multiple splits, we'll concatenate them to get the full raw data
        if len(splits) > 1:
            logger.info(f"Dataset has multiple splits: {splits}. Concatenating all.")
            full_dataset = dataset[splits[0]]
            for split in splits[1:]:
                full_dataset = full_dataset.concatenate(dataset[split])
        else:
            full_dataset = dataset[splits[0]]
            logger.info(f"Dataset has single split: {splits[0]}")

        # Convert to Pandas DataFrame for efficient Parquet writing
        df = full_dataset.to_pandas()
        
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

        # Save to Parquet
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Successfully saved raw data to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download or save the dataset: {e}")
        raise

def main():
    """Entry point for the download script."""
    success = download_oqmd_dataset()
    if success:
        logger.info("Download task completed successfully.")
        sys.exit(0)
    else:
        logger.error("Download task failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
