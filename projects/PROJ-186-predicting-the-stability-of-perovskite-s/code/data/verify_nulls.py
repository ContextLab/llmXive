"""
Verification script for T019.
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

def main():
    logger = get_logger(__name__)
    log_pipeline_event(logger, "Starting verification of decomposition_energy nulls (T019)")

    data_path = project_root / "data" / "processed" / "features.csv"

    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        print(f"FAIL: File not found at {data_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        print(f"FAIL: Could not read CSV: {e}")
        sys.exit(1)

    if "decomposition_energy" not in df.columns:
        logger.error("Column 'decomposition_energy' not found in features.csv")
        print("FAIL: Column 'decomposition_energy' not found")
        sys.exit(1)

    null_count = df["decomposition_energy"].isna().sum()
    total_count = len(df)

    log_pipeline_event(logger, f"Checked {total_count} rows. Null count: {null_count}")

    if null_count == 0:
        print(f"SUCCESS: Zero nulls found in 'decomposition_energy' column ({total_count} rows checked).")
        logger.info("Verification passed: Zero nulls in decomposition_energy")
        sys.exit(0)
    else:
        print(f"FAIL: Found {null_count} nulls in 'decomposition_energy' column out of {total_count} rows.")
        logger.error(f"Verification failed: {null_count} nulls found in decomposition_energy")
        sys.exit(1)

if __name__ == "__main__":
    main()