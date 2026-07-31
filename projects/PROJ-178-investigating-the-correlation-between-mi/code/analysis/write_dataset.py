"""
write_dataset.py

Implements T020: Write processed dataset to code/data/processed/mito_aging_dataset.csv
with checksum generation.

This module is the final step of User Story 1, taking the merged and filtered
dataset and persisting it to disk with a SHA-256 checksum for data integrity.
"""

import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path

# Import from sibling modules as per API surface
from config.environment import ensure_directories, get_local_paths

logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest string.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: file not found at {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def write_processed_dataset(df: pd.DataFrame, output_path: Path, checksum_path: Path = None) -> dict:
    """
    Write the processed dataset to CSV and optionally generate a checksum file.

    Args:
        df: The processed DataFrame to write.
        output_path: Path where the CSV file will be saved.
        checksum_path: Optional path for the checksum file. If None, a .sha256 file
                       will be created next to the output CSV.

    Returns:
        Dictionary containing 'output_path', 'checksum_path', and 'checksum'.
    """
    if df.empty:
        raise ValueError("Cannot write an empty dataset. Check upstream filtering logic.")

    # Ensure output directory exists
    ensure_directories([output_path.parent])

    logger.info(f"Writing processed dataset to {output_path}")
    df.to_csv(output_path, index=False)

    # Calculate checksum
    checksum = calculate_file_checksum(output_path)
    logger.info(f"Dataset checksum (SHA-256): {checksum}")

    # Write checksum to file
    if checksum_path is None:
        checksum_path = output_path.with_suffix(output_path.suffix + '.sha256')
    
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    
    logger.info(f"Checksum written to {checksum_path}")

    return {
        'output_path': str(output_path),
        'checksum_path': str(checksum_path),
        'checksum': checksum
    }

def main():
    """
    Main entry point for the write_dataset script.
    
    This function loads the merged dataset from the intermediate location
    (produced by merge_metadata.py), performs final validation, and writes
    it to the final processed location with a checksum.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get paths from environment config
    paths = get_local_paths()
    processed_dir = paths['processed_dir']
    interim_merge_path = paths.get('interim_merge_path', processed_dir / 'interim_merged_dataset.csv')
    final_output_path = processed_dir / 'mito_aging_dataset.csv'

    # Check if interim file exists
    if not interim_merge_path.exists():
        logger.error(f"Interim merged dataset not found at {interim_merge_path}")
        logger.error("Please ensure T018 (merge_metadata.py) has completed successfully.")
        sys.exit(1)

    try:
        # Load the merged dataset
        logger.info(f"Loading interim dataset from {interim_merge_path}")
        df = pd.read_csv(interim_merge_path)
        
        # Log basic stats
        logger.info(f"Loaded dataset with {len(df)} samples and {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        # Write to final location
        result = write_processed_dataset(df, final_output_path)

        logger.info("Task T020 completed successfully.")
        logger.info(f"Final output: {result['output_path']}")
        logger.info(f"Checksum: {result['checksum']}")

        return 0

    except Exception as e:
        logger.exception(f"Error during dataset writing: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
