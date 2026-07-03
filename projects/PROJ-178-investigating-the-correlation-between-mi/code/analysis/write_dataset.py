"""
Task T020: Write processed dataset to code/data/processed/mito_aging_dataset.csv with checksum generation.

This script takes the merged and cleaned dataset produced by previous steps (T018, T019),
writes it to a CSV file, and generates a SHA-256 checksum for data integrity verification.
"""
import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.clean_dataset import clean_dataset, main as clean_main
from analysis.merge_metadata import merge_datasets, main as merge_main

logger = logging.getLogger(__name__)

def calculate_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """Calculate checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def write_processed_dataset(output_path: str) -> str:
    """
    Write the processed dataset to CSV and generate checksum.

    Args:
        output_path: Path to the output CSV file.

    Returns:
        The SHA-256 checksum of the written file.
    """
    logger.info(f"Writing processed dataset to {output_path}")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the merged dataset (this assumes previous steps have created the intermediate files)
    # The merge_datasets function returns the merged DataFrame
    merged_df = merge_datasets()

    if merged_df is None or merged_df.empty:
        raise ValueError("Merged dataset is empty or None. Previous steps may have failed.")

    # Write to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(merged_df)} rows to {output_path}")

    # Calculate and write checksum
    checksum = calculate_file_checksum(output_path)
    checksum_path = str(output_path) + ".sha256"
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(output_path)}\n")
    
    logger.info(f"Generated checksum: {checksum}")
    logger.info(f"Checksum saved to {checksum_path}")

    return checksum

def main():
    """Main entry point for T020."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define output path as per task specification
    output_path = str(Path(__file__).parent.parent / "data" / "processed" / "mito_aging_dataset.csv")

    try:
        checksum = write_processed_dataset(output_path)
        logger.info(f"Task T020 completed successfully. Dataset: {output_path}, Checksum: {checksum}")
        return 0
    except Exception as e:
        logger.error(f"Task T020 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
