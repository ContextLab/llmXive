"""
Verification script for Task T018.
Verifies that data/processed/features.csv has zero nulls in the decomposition_energy column.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

def main():
    """
    Main entry point for verification.
    Loads data/processed/features.csv and asserts zero nulls in decomposition_energy.
    """
    data_path = project_root / "data" / "processed" / "features.csv"

    if not data_path.exists():
        error_msg = f"Required artifact missing: {data_path}. " \
                    f"Please ensure T017 (preprocess.py) has run successfully."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Loading {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        error_msg = f"Failed to load {data_path}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Loaded dataset with shape: {df.shape}")

    target_column = "decomposition_energy"

    if target_column not in df.columns:
        error_msg = f"Target column '{target_column}' not found in {data_path}. " \
                    f"Available columns: {list(df.columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    null_count = df[target_column].isnull().sum()

    logger.info(f"Null count in '{target_column}': {null_count}")

    if null_count > 0:
        error_msg = f"Verification FAILED: Found {null_count} null values in '{target_column}'."
        logger.error(error_msg)
        raise AssertionError(error_msg)

    log_pipeline_event("T018_VERIFICATION", f"SUCCESS: Zero nulls in '{target_column}'")
    logger.info("Verification PASSED: Zero nulls in decomposition_energy column.")
    print("PASS: Zero nulls in target")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Verification failed with exception")
        sys.exit(1)
