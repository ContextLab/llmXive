import os
import sys
import logging
import pandas as pd
from pathlib import Path
from utils.logging import setup_logger

def validate_metadata_columns(metadata_path: str, required_columns: list) -> bool:
    """
    Verify the presence of required columns in the downloaded metadata CSV.

    Args:
        metadata_path: Path to the metadata CSV file (e.g., data/raw/metadata.csv)
        required_columns: List of column names that must be present.

    Returns:
        True if all columns are present, False otherwise.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
        SystemExit: If required columns are missing (Fatal Gate).
    """
    logger = setup_logger(__name__)
    
    if not os.path.exists(metadata_path):
        logger.error(f"Fatal: Metadata file not found at {metadata_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(metadata_path)
        available_columns = set(df.columns)
        missing_columns = [col for col in required_columns if col not in available_columns]

        if missing_columns:
            error_msg = f"Fatal: Dataset lacks behavioral motor task metrics. Missing columns: {missing_columns}"
            logger.error(error_msg)
            # Fatal Gate: Exit immediately, do not proceed
            sys.exit(1)
        
        logger.info(f"Validation passed. All required columns present: {required_columns}")
        return True

    except pd.errors.EmptyDataError:
        logger.error("Fatal: Metadata file is empty.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal: Error reading metadata file: {e}")
        sys.exit(1)

def main():
    """
    Entry point for the validation gate task (T002).
    Checks for required columns in data/raw/metadata.csv.
    """
    logger = setup_logger(__name__)
    logger.info("Starting T002: Fatal Gate - Metadata Column Validation")

    # Define paths relative to project root
    # Assuming the script is run from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent.parent
    metadata_path = project_root / "data" / "raw" / "metadata.csv"
    
    required_columns = [
        "pre_motor_score", 
        "post_motor_score", 
        "age", 
        "sex", 
        "subject_id"
    ]

    logger.info(f"Checking metadata at: {metadata_path}")
    logger.info(f"Required columns: {required_columns}")

    # Perform validation (exits on failure)
    validate_metadata_columns(str(metadata_path), required_columns)
    
    logger.info("T002 Validation Gate PASSED. Proceeding to next tasks.")

if __name__ == "__main__":
    main()
