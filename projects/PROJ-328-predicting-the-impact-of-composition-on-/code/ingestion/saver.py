import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from ingestion.aggregator import LiteratureAggregator
from ingestion.cleaner import DataCleaner
from ingestion.validator import DataValidator
from config import get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_raw_data_with_checksums(
    df: pd.DataFrame,
    raw_output_path: Path,
    checksum_output_path: Path
) -> None:
    """
    Save the dataframe to a CSV file and generate a checksum file.
    
    This function:
    1. Ensures the output directory exists.
    2. Saves the DataFrame to a CSV file (immutable raw data).
    3. Calculates the MD5 checksum of the saved file.
    4. Writes the filename and checksum to a text file.
    
    Args:
        df: The DataFrame containing the raw solder hardness data.
        raw_output_path: Path to the output CSV file.
        checksum_output_path: Path to the output checksum text file.
    
    Raises:
        IOError: If the file cannot be written.
    """
    # Ensure directory exists
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving raw data to {raw_output_path}")
    
    # Save to CSV
    # Use index=False to avoid saving the pandas index as a column
    df.to_csv(raw_output_path, index=False)
    
    # Verify file was written
    if not raw_output_path.exists():
        raise IOError(f"Failed to write file: {raw_output_path}")
    
    # Calculate checksum
    checksum = calculate_md5(raw_output_path)
    logger.info(f"Checksum for {raw_output_path.name}: {checksum}")
    
    # Write checksum file
    # Format: <filename> <checksum>
    with open(checksum_output_path, 'w') as f:
        f.write(f"{raw_output_path.name} {checksum}\n")
    
    logger.info(f"Checksum saved to {checksum_output_path}")

def main():
    """
    Main entry point for the raw data saving task (T015).
    
    This function orchestrates the full ingestion pipeline up to the saving stage:
    1. Aggregates data from literature sources.
    2. Cleans the data (filtering, standardization).
    3. Validates the data (non-null, composition sums).
    4. Saves the validated raw data to `data/raw/solder_hardness_raw.csv`.
    5. Generates `data/checksums.txt`.
    """
    logger.info("Starting T015: Save raw immutable data with checksums")
    
    # 1. Aggregation
    # Note: T012 implementation is assumed to be present in code/ingestion/aggregator.py
    aggregator = LiteratureAggregator()
    raw_df = aggregator.run()
    
    if raw_df is None or raw_df.empty:
        logger.error("Aggregation returned no data. Cannot proceed with saving.")
        # In a real pipeline, we might raise an exception here
        return
    
    logger.info(f"Aggregated {len(raw_df)} records.")
    
    # 2. Cleaning
    # Note: T013 implementation is assumed to be present in code/ingestion/cleaner.py
    cleaner = DataCleaner()
    cleaned_df = cleaner.run(raw_df)
    
    if cleaned_df is None or cleaned_df.empty:
        logger.error("Cleaning resulted in an empty dataset. Cannot proceed with saving.")
        return
    
    logger.info(f"Cleaned data contains {len(cleaned_df)} records.")
    
    # 3. Validation
    # Note: T014 implementation is assumed to be present in code/ingestion/validator.py
    validator = DataValidator()
    validated_df = validator.run(cleaned_df)
    
    if validated_df is None or validated_df.empty:
        logger.error("Validation failed or resulted in empty dataset. Cannot proceed with saving.")
        return
    
    logger.info(f"Validated data contains {len(validated_df)} records.")
    
    # 4. Save Raw Data
    raw_output_path = get_data_raw_dir() / "solder_hardness_raw.csv"
    checksum_output_path = Path("data/checksums.txt")
    
    save_raw_data_with_checksums(validated_df, raw_output_path, checksum_output_path)
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()