import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path
from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate the checksum of a file to ensure data integrity.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: md5)
        
    Returns:
        Hexadecimal string of the checksum
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def write_processed_dataset(df: pd.DataFrame, output_path: str) -> dict:
    """
    Write the processed dataset to CSV and generate a checksum.
    
    Args:
        df: The processed DataFrame to write
        output_path: Path where the CSV file will be saved
        
    Returns:
        Dictionary containing the output path and checksum
    """
    # Ensure directory exists
    ensure_directories([str(Path(output_path).parent)])
    
    # Write to CSV
    logger.info(f"Writing processed dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Calculate checksum
    checksum = calculate_file_checksum(output_path)
    logger.info(f"Generated checksum for {output_path}: {checksum}")
    
    return {
        'path': output_path,
        'checksum': checksum,
        'rows': len(df),
        'columns': len(df.columns)
    }

def main():
    """
    Main entry point for writing the processed dataset.
    This function assumes that previous steps (T018, T019) have already
    produced the merged and filtered DataFrame in memory or a temporary location.
    For this task, we will load the intermediate results from the merge step
    (assumed to be in code/data/processed/merged_data.csv if T018 was completed)
    or re-run the merge logic if necessary.
    
    However, since T018 and T019 are marked as needing redo, we will implement
    a robust solution that attempts to load the merged data from the expected
    location. If it doesn't exist, we will raise an error to prevent silent failure.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths from environment
    paths = get_local_paths()
    output_dir = paths['processed_data']
    output_file = os.path.join(output_dir, 'mito_aging_dataset.csv')
    
    # Check if we have the merged data from T018/T019
    # The merge step should have produced a file with burden, haplogroup, age, sex, etc.
    # Since T018/T019 are incomplete, we need to ensure the data exists
    # In a real scenario, this would be loaded from the output of T019
    
    # For now, we'll assume the merge logic from T018/T019 has been implemented
    # and the data is available in a temporary location or we need to re-run the merge
    
    # Attempt to load the merged data (this assumes T018/T019 produced this file)
    merged_data_path = os.path.join(output_dir, 'merged_data.csv')
    
    if not os.path.exists(merged_data_path):
        logger.error(f"Merged data file not found at {merged_data_path}. "
                    "Please ensure T018 and T019 have been completed successfully.")
        # In a real implementation, we might re-run the merge logic here
        # But for this task, we'll fail loudly as per requirements
        raise FileNotFoundError(
            f"Merged data file not found at {merged_data_path}. "
            "T018 (metadata merge) and T019 (exclusion logic) must be completed first."
        )
    
    # Load the merged data
    logger.info(f"Loading merged data from {merged_data_path}")
    df = pd.read_csv(merged_data_path)
    
    # Verify critical columns exist
    required_columns = ['sample_id', 'burden', 'haplogroup', 'age', 'sex', 'population']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Write the final processed dataset
    result = write_processed_dataset(df, output_file)
    
    logger.info(f"Successfully wrote processed dataset: {result}")
    return result

if __name__ == '__main__':
    main()
