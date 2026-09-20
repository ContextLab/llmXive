"""
Script to verify the output schema of unified_timeseries.csv as per T038.
Checks for required columns and correct data types.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_output_schema")

def verify_schema(file_path: Path) -> bool:
    """
    Verify that the CSV file has the correct columns and data types.
    
    Expected columns:
    - date: datetime
    - rigidity_bin: float
    - proton_flux: float
    - helium_flux: float
    - heavy_flux: float
    - sunspot_number: int
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False

    required_columns = {
        'date': 'datetime64[ns]',
        'rigidity_bin': 'float64',
        'proton_flux': 'float64',
        'helium_flux': 'float64',
        'heavy_flux': 'float64',
        'sunspot_number': 'int64'
    }

    # Check for missing columns
    missing_cols = set(required_columns.keys()) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        logger.info(f"Available columns: {list(df.columns)}")
        return False

    # Check data types
    all_correct = True
    for col, expected_dtype in required_columns.items():
        actual_dtype = str(df[col].dtype)
        if actual_dtype != expected_dtype:
            # Special handling for date column which might be parsed as object if not converted
            if col == 'date' and 'datetime' in actual_dtype:
                logger.warning(f"Column '{col}' has dtype {actual_dtype}, expected {expected_dtype}. Attempting conversion.")
                try:
                    df[col] = pd.to_datetime(df[col])
                    logger.info(f"Successfully converted '{col}' to datetime.")
                except Exception as e:
                    logger.error(f"Failed to convert '{col}' to datetime: {e}")
                    all_correct = False
            else:
                logger.error(f"Column '{col}' has incorrect dtype: {actual_dtype} (expected {expected_dtype})")
                all_correct = False
        else:
            logger.info(f"Column '{col}' has correct dtype: {actual_dtype}")

    if not all_correct:
        logger.error("Schema verification FAILED.")
        return False

    logger.info("Schema verification PASSED.")
    logger.info(f"Sample data:\n{df.head()}")
    return True

def main():
    # Define path relative to project root
    project_root = Path(__file__).resolve().parent.parent
    output_file = project_root / "data" / "processed" / "unified_timeseries.csv"
    
    logger.info(f"Verifying output schema for: {output_file}")
    success = verify_schema(output_file)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
