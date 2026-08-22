"""
Verification script for T018.
Verifies that data/processed/features.csv has zero nulls in the decomposition_energy column.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

def main():
    """
    Execute the verification for T018.
    Loads data/processed/features.csv and asserts decomposition_energy has no nulls.
    """
    data_path = project_root / "data" / "processed" / "features.csv"

    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        log_pipeline_event("VERIFICATION_FAILED", f"File {data_path} does not exist.")
        print(f"FAIL: {data_path} not found.")
        sys.exit(1)

    try:
        logger.info(f"Loading {data_path}...")
        df = pd.read_csv(data_path)
        
        if df.empty:
            logger.error("Dataset is empty.")
            log_pipeline_event("VERIFICATION_FAILED", "Dataset is empty.")
            print("FAIL: Dataset is empty.")
            sys.exit(1)

        # Check for nulls in decomposition_energy
        null_count = df['decomposition_energy'].isnull().sum()
        
        logger.info(f"Total rows: {len(df)}")
        logger.info(f"Nulls in 'decomposition_energy': {null_count}")

        if null_count > 0:
            error_msg = f"FAIL: Found {null_count} nulls in 'decomposition_energy' column."
            logger.error(error_msg)
            log_pipeline_event("VERIFICATION_FAILED", error_msg)
            print(error_msg)
            sys.exit(1)
        else:
            success_msg = "PASS: Zero nulls in 'decomposition_energy' column."
            logger.info(success_msg)
            log_pipeline_event("VERIFICATION_SUCCESS", success_msg)
            print(success_msg)
            # Explicitly exit with 0 to ensure the task is marked complete
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Error during verification: {e}")
        log_pipeline_event("VERIFICATION_ERROR", str(e))
        print(f"FAIL: Error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()