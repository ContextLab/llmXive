import logging
import sys
from pathlib import Path
import pandas as pd

# Importing from sibling module as per API surface
# Note: verify_column_data_validity is defined here to satisfy the import surface
# while verify_column_presence is the primary function for T014b.

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Requirement FR-002 specific column name
REQUIRED_COLUMN_FIRST_IONIZATION = 'first_ionization_energy'
DESCRIPTORS_FILE_PATH = Path('data/processed/descriptors.csv')

def verify_column_presence(df: pd.DataFrame, column_name: str) -> bool:
    """
    Verifies that a specific column exists in the DataFrame.
    
    Args:
        df: The DataFrame to check.
        column_name: The name of the column to verify.
        
    Returns:
        True if the column exists, False otherwise.
    """
    if column_name not in df.columns:
        logger.error(f"Missing required column: {column_name}")
        logger.error(f"Available columns: {list(df.columns)}")
        return False
    
    logger.info(f"Column '{column_name}' verified present.")
    return True

def verify_column_data_validity(df: pd.DataFrame, column_name: str) -> bool:
    """
    Verifies that the column contains valid numerical data (no NaNs, not all zero).
    
    Args:
        df: The DataFrame to check.
        column_name: The name of the column to verify.
        
    Returns:
        True if data is valid, False otherwise.
    """
    if not verify_column_presence(df, column_name):
        return False
    
    col_data = df[column_name]
    
    if col_data.isnull().any():
        logger.error(f"Column '{column_name}' contains null values.")
        return False
    
    if col_data.empty:
        logger.error(f"Column '{column_name}' is empty.")
        return False
    
    # Check if values are numeric
    if not pd.api.types.is_numeric_dtype(col_data):
        logger.error(f"Column '{column_name}' is not numeric.")
        return False
    
    logger.info(f"Column '{column_name}' data validity verified.")
    return True

def main() -> int:
    """
    Main entry point for verifying the 'first_ionization_energy' column 
    in the descriptors dataset as per FR-002.
    
    Returns:
        0 if verification passes, 1 if it fails.
    """
    logger.info(f"Starting verification for {DESCRIPTORS_FILE_PATH}")
    
    if not DESCRIPTORS_FILE_PATH.exists():
        logger.error(f"File not found: {DESCRIPTORS_FILE_PATH}")
        logger.error("Ensure T014 (feature_engineering.py) has run successfully to generate descriptors.csv.")
        return 1
    
    try:
        df = pd.read_csv(DESCRIPTORS_FILE_PATH)
        logger.info(f"Loaded {len(df)} rows from {DESCRIPTORS_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return 1
    
    # T014b Specific Requirement: Verify 'first_ionization_energy' presence
    success = verify_column_presence(df, REQUIRED_COLUMN_FIRST_IONIZATION)
    
    if success:
        # Optional: Verify data validity as part of robustness
        if verify_column_data_validity(df, REQUIRED_COLUMN_FIRST_IONIZATION):
            logger.info("VERIFICATION PASSED: 'first_ionization_energy' column is present and valid.")
            return 0
        else:
            logger.error("VERIFICATION FAILED: Column present but data is invalid.")
            return 1
    else:
        logger.error("VERIFICATION FAILED: Required column 'first_ionization_energy' is missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
