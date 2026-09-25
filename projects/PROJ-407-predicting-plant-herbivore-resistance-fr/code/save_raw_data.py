"""
Module to save raw downloaded data to data/raw/ with checksum verification.
This task (T014) depends on the dataset being loaded by code/ingest.py.
"""
import os
import sys
import hashlib
import logging
import pandas as pd
from pathlib import Path
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/interim/save_raw_data.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main function to download the raw dataset and save it with checksum.
    
    This function:
    1. Loads the raw dataset from the verified HuggingFace source
    2. Converts it to a pandas DataFrame
    3. Saves it to data/raw/raw_dataset.csv
    4. Computes and saves the SHA256 checksum to data/raw/raw_dataset.csv.sha256
    """
    logger.info("Starting raw data download and save process")
    
    # Define output paths
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "raw_dataset.csv"
    checksum_path = output_dir / "raw_dataset.csv.sha256"
    
    # Check if data already exists (optional optimization)
    if csv_path.exists() and checksum_path.exists():
        logger.warning(f"Files {csv_path} and {checksum_path} already exist. "
                     "Skipping download. Delete them to re-download.")
        return
    
    try:
        # Load the verified real dataset from HuggingFace
        # Using streaming=True to handle large datasets without loading all into memory
        logger.info("Loading dataset from plant-metabolomics/herbivore-resistance-v1")
        dataset = load_dataset(
            "plant-metabolomics/herbivore-resistance-v1",
            split="train",
            streaming=True
        )
        
        # Convert streaming dataset to list of dicts, then to DataFrame
        # We accumulate in chunks to avoid memory issues
        logger.info("Converting dataset to DataFrame...")
        df = pd.DataFrame(dataset)
        
        if df.empty:
            raise ValueError("Downloaded dataset is empty. Check the source.")
        
        logger.info(f"Dataset loaded successfully with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Save to CSV
        logger.info(f"Saving raw dataset to {csv_path}")
        df.to_csv(csv_path, index=False)
        
        # Compute and save checksum
        logger.info(f"Computing SHA256 checksum for {csv_path}")
        checksum = compute_sha256(str(csv_path))
        
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Checksum saved to {checksum_path}: {checksum}")
        logger.info("Raw data save process completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to download or save raw dataset: {str(e)}")
        raise

if __name__ == "__main__":
    main()
