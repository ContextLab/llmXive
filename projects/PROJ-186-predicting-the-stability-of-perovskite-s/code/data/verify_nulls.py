"""
Verification script for User Story 1 (T017).
Checks that data/processed/features.csv has zero nulls in the 'decomposition_energy' column.
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
    Load data/processed/features.csv and verify 'decomposition_energy' has no nulls.
    Exits with code 0 on success, 1 on failure.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "processed" / "features.csv"

    log_pipeline_event("Starting verification of decomposition_energy nulls")
    logger.info(f"Loading data from: {data_path}")

    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        log_pipeline_event("Verification FAILED: File not found")
        sys.exit(1)

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        log_pipeline_event("Verification FAILED: CSV load error")
        sys.exit(1)

    if "decomposition_energy" not in df.columns:
        logger.error("Column 'decomposition_energy' not found in CSV")
        log_pipeline_event("Verification FAILED: Missing column")
        sys.exit(1)

    null_count = df["decomposition_energy"].isnull().sum()
    total_count = len(df)

    logger.info(f"Total rows: {total_count}, Nulls in 'decomposition_energy': {null_count}")

    if null_count == 0:
        logger.info("SUCCESS: Zero nulls found in 'decomposition_energy' column.")
        log_pipeline_event("Verification PASSED: Zero nulls in decomposition_energy")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: Found {null_count} nulls in 'decomposition_energy' column.")
        log_pipeline_event("Verification FAILED: Non-zero nulls in decomposition_energy")
        sys.exit(1)

if __name__ == "__main__":
    main()