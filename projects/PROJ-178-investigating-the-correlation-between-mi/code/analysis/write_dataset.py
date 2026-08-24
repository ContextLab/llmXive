import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path

from config.environment import get_local_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'md5') -> str:
    """
    Calculate the checksum of a file to ensure data integrity.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: md5).

    Returns:
        Hex digest string of the file checksum.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: file not found at {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def write_processed_dataset(df: pd.DataFrame, output_path: Path) -> str:
    """
    Write the processed dataset to a CSV file and generate a checksum.

    Args:
        df: The pandas DataFrame containing the processed dataset.
        output_path: The path where the CSV file will be written.

    Returns:
        The checksum of the written file.
    """
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing processed dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Dataset written successfully. Shape: {df.shape}")
    
    # Calculate and log checksum
    checksum = calculate_file_checksum(output_path)
    logger.info(f"Checksum ({output_path.name}): {checksum}")
    
    return checksum

def main():
    """
    Main entry point for writing the processed dataset and generating checksum.
    This script assumes that the processed dataset has already been created
    by previous steps (e.g., T018) and is available at the expected location.
    It will load the data, write it to the final output location, and generate a checksum.
    """
    paths = get_local_paths()
    
    # Define input and output paths
    # T018 was supposed to write to this location, but if it failed or we need to re-write,
    # we assume the data is available in the processed directory.
    # Since T018 was marked as failed/missing in the feedback, we assume the data
    # might need to be regenerated or re-merged. However, T020's specific job is
    # to write the dataset and generate checksum. 
    # We will assume the merged data exists at the expected path from T018's description.
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    output_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found at {input_path}.")
        logger.error("This task depends on T018 completing successfully to generate the input file.")
        sys.exit(1)

    try:
        logger.info(f"Loading dataset from {input_path}")
        df = pd.read_csv(input_path)
        
        if df.empty:
            logger.warning("Dataset is empty. Writing empty file.")
        else:
            logger.info(f"Loaded dataset with {len(df)} samples and {len(df.columns)} columns.")
            # Verify critical columns exist (optional validation)
            critical_columns = ['sample_id', 'age', 'sex', 'population', 'haplogroup', 'burden']
            missing_cols = [col for col in critical_columns if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing critical columns: {missing_cols}")

        # Write to final output location (could be same as input if overwriting)
        checksum = write_processed_dataset(df, output_path)
        
        # Optionally write checksum to a separate file for easy access
        checksum_path = paths['processed_data'] / 'mito_aging_dataset.csv.md5'
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        logger.info(f"Checksum written to {checksum_path}")

    except Exception as e:
        logger.error(f"Error processing dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
