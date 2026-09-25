"""
T002: Fatal Gate - Verify required columns in downloaded metadata.

This script checks for the presence of essential behavioral columns
in the metadata downloaded by T001. If any required column is missing,
it logs a fatal error and exits immediately, preventing downstream
processing of invalid data.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import setup_logger
from utils.config import get_config

REQUIRED_COLUMNS = ['pre_motor_score', 'post_motor_score', 'age', 'sex', 'subject_id']
METADATA_PATH = Path("data/raw/metadata.csv")

def validate_metadata_columns(file_path: Path) -> bool:
    """
    Verify that the metadata file contains all required columns.
    
    Args:
        file_path: Path to the metadata CSV file.
        
    Returns:
        True if all required columns are present, False otherwise.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    logger = logging.getLogger("validation_gate")
    
    if not file_path.exists():
        logger.error(f"Fatal: Metadata file not found at {file_path}")
        return False
        
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Fatal: Could not read metadata file: {e}")
        return False
        
    if df.empty:
        logger.error("Fatal: Metadata file is empty (no rows).")
        return False
        
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Fatal: Dataset lacks behavioral motor task metrics. Missing columns: {missing_cols}")
        return False
        
    logger.info(f"Validation passed: All {len(REQUIRED_COLUMNS)} required columns present.")
    return True

def main():
    """Main entry point for the validation gate."""
    setup_logger("validation_gate", level=logging.INFO)
    logger = logging.getLogger("validation_gate")
    
    logger.info("Starting T002: Fatal Gate - Metadata Column Verification")
    
    # Use configured path or default
    config = get_config()
    # Default to data/raw/metadata.csv if not specified in config
    meta_path = METADATA_PATH
    
    if not validate_metadata_columns(meta_path):
        logger.critical("FATAL: Aborting pipeline due to missing behavioral metrics.")
        sys.exit(1)
        
    logger.info("T002 completed successfully. Proceeding to next phase.")
    return 0

if __name__ == "__main__":
    sys.exit(main())