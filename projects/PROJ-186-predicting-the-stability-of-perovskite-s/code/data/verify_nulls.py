"""
Verification script for T019: Ensure data/processed/features.csv has zero nulls
in the 'decomposition_energy' column.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

def main():
    """
    Load data/processed/features.csv and verify that the 'decomposition_energy'
    column contains zero null values.
    Exits with code 1 if nulls are found or file is missing.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    features_path = project_root / "data" / "processed" / "features.csv"

    log_pipeline_event(f"Verifying nulls in {features_path}")

    # Check if file exists
    if not features_path.exists():
        logger.error(f"File not found: {features_path}")
        print(f"FAIL: {features_path} does not exist.")
        sys.exit(1)

    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        print(f"FAIL: Could not read {features_path}. Error: {e}")
        sys.exit(1)

    # Check if target column exists
    target_column = "decomposition_energy"
    if target_column not in df.columns:
        logger.error(f"Column '{target_column}' not found in {features_path}")
        print(f"FAIL: Column '{target_column}' not found in {features_path}.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Count nulls
    null_count = df[target_column].isnull().sum()
    total_rows = len(df)

    log_pipeline_event(f"Checked {total_rows} rows. Found {null_count} nulls in '{target_column}'.")

    if null_count > 0:
        logger.error(f"Verification FAILED: Found {null_count} null values in '{target_column}'.")
        print(f"FAIL: Found {null_count} null values in '{target_column}' column.")
        # Optionally show indices of nulls for debugging
        null_indices = df[df[target_column].isnull()].index.tolist()
        print(f"Indices with nulls: {null_indices[:10]}... (showing first 10)")
        sys.exit(1)
    else:
        logger.info(f"Verification PASSED: Zero null values in '{target_column}'.")
        print(f"SUCCESS: '{target_column}' column has zero null values ({total_rows} valid entries).")
        sys.exit(0)

if __name__ == "__main__":
    main()
