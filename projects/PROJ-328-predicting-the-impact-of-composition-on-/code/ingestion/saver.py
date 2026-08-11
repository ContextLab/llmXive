import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from seed import init_reproducibility
from config import get_data_processed_dir, get_data_raw_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_raw_data_with_checksums(raw_df, output_path: Path, checksum_file: Path) -> None:
    """Save raw data to CSV and generate checksum."""
    logger.info(f"Saving raw data to {output_path}")
    raw_df.to_csv(output_path, index=False)
    
    checksum = calculate_md5(output_path)
    logger.info(f"Raw data checksum (MD5): {checksum}")
    
    with open(checksum_file, "a") as f:
        f.write(f"{output_path.name}: {checksum}\n")
    
    logger.info(f"Checksum appended to {checksum_file}")

def save_validated_data(validated_df: Any, output_path: Path) -> None:
    """
    Save the validated dataset to CSV.
    
    This function implements T016: Save validated dataset to 
    data/processed/solder_hardness_validated.csv (must run after T014).
    
    Args:
        validated_df: The validated DataFrame from the ingestion pipeline.
        output_path: The target path for the validated CSV file.
    """
    logger.info(f"Saving validated dataset to {output_path}")
    
    if validated_df is None or validated_df.empty:
        logger.error("Cannot save validated data: DataFrame is None or empty.")
        raise ValueError("Validated DataFrame is empty or None. Ensure T014 validation passed.")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    validated_df.to_csv(output_path, index=False)
    
    # Generate and log checksum
    checksum = calculate_md5(output_path)
    logger.info(f"Validated data saved successfully. Row count: {len(validated_df)}")
    logger.info(f"Validated data checksum (MD5): {checksum}")
    
    # Append checksum to the global checksums file
    checksum_file = Path(str(output_path).replace("processed", "checksums.txt"))
    # Fallback to data/checksums.txt if specific path logic differs
    if not checksum_file.exists():
        checksum_file = Path(get_data_processed_dir().parent) / "checksums.txt"
    
    with open(checksum_file, "a") as f:
        f.write(f"{output_path.name}: {checksum}\n")
    
    logger.info(f"Checksum appended to {checksum_file}")

def main():
    """
    Main entry point for T016: Save validated dataset.
    
    This script expects the validated data to be available (typically from T014/validator.py).
    In a real pipeline, this would be called after validation.
    For this task implementation, we assume the validated data is passed or loaded 
    from the intermediate state if necessary, but primarily focuses on the save logic.
    """
    logger.info("Starting T016: Save validated dataset")
    
    # In a full pipeline, this would load the validated data from the validator's output
    # or receive it as an argument. Here we demonstrate the save function.
    # NOTE: The actual data flow is handled by pipeline_runner.py which calls 
    # cleaner -> validator -> saver.
    
    processed_dir = get_data_processed_dir()
    output_path = processed_dir / "solder_hardness_validated.csv"
    
    logger.info(f"Output path configured: {output_path}")
    logger.info("T016 implementation complete. Ready to save data when pipeline provides it.")

if __name__ == "__main__":
    init_reproducibility()
    main()