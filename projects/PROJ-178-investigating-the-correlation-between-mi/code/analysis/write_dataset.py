import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path

# Import from existing API surface
from config.environment import ensure_directories, get_local_paths
from analysis.merge_metadata import main as merge_metadata_main

logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file to ensure data integrity.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the file checksum
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def write_processed_dataset(df: pd.DataFrame, output_path: Path, checksum_path: Path = None) -> None:
    """
    Write the processed dataset to CSV and generate a checksum file.
    
    Args:
        df: The processed DataFrame to write
        output_path: Path where the CSV file will be saved
        checksum_path: Optional path for the checksum file (defaults to output_path + '.sha256')
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the dataset to CSV
    logger.info(f"Writing processed dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Calculate and write checksum
    if checksum_path is None:
        checksum_path = Path(str(output_path) + '.sha256')
    
    checksum = calculate_file_checksum(output_path)
    logger.info(f"Generated checksum: {checksum}")
    
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    
    logger.info(f"Checksum written to {checksum_path}")

def main():
    """
    Main entry point for writing the processed dataset.
    
    This function:
    1. Loads the merged dataset (produced by merge_metadata.py)
    2. Performs final validation (checks for missing values in critical columns)
    3. Writes the dataset to code/data/processed/mito_aging_dataset.csv
    4. Generates a SHA256 checksum file
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure directories exist
    ensure_directories()
    
    # Get paths from environment config
    local_paths = get_local_paths()
    processed_dir = local_paths['processed']
    output_file = processed_dir / 'mito_aging_dataset.csv'
    
    # Load the merged dataset
    # The merge_metadata module produces 'merged_dataset.csv' in the processed directory
    merged_input = processed_dir / 'merged_dataset.csv'
    
    if not merged_input.exists():
        logger.error(f"Input file not found: {merged_input}")
        logger.error("Please ensure T018 (merge_metadata) has been run successfully.")
        sys.exit(1)
    
    logger.info(f"Loading merged dataset from {merged_input}")
    try:
        df = pd.read_csv(merged_input)
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        sys.exit(1)
    
    # Final validation: check for missing values in critical columns
    critical_columns = ['sample_id', 'burden', 'age', 'haplogroup', 'sex', 'population']
    missing_cols = [col for col in critical_columns if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing critical columns in dataset: {missing_cols}")
        sys.exit(1)
    
    # Check for missing values in critical columns
    for col in critical_columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            logger.error(f"Found {null_count} missing values in critical column '{col}'")
            sys.exit(1)
    
    logger.info(f"Validation passed. Dataset shape: {df.shape}")
    
    # Write the processed dataset
    write_processed_dataset(df, output_file)
    
    logger.info(f"Successfully wrote processed dataset to {output_file}")
    logger.info(f"Checksum file created at {output_file}.sha256")

if __name__ == "__main__":
    main()