"""
T013e: Verify Volume Constraint (SC-001).

Post-processing check to ensure the pipeline ingested >1,000 unique 2D material
entries. If the count is < 1,000, exit with code 1 and log a critical error.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def count_unique_entries(parquet_path: Path) -> int:
    """
    Count the number of unique material entries in the parquet file.
    Uniqueness is determined by the 'id' column.
    """
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        return 0

    try:
        df = pd.read_parquet(parquet_path)
        if df.empty:
            logger.warning("Parquet file is empty.")
            return 0

        if 'id' not in df.columns:
            logger.error("Parquet file does not contain 'id' column.")
            return 0

        unique_count = df['id'].nunique()
        return int(unique_count)
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        return 0

def verify_volume_constraint(
    parquet_path: Path,
    threshold: int = 1000
) -> bool:
    """
    Verify that the number of unique entries meets the threshold (SC-001).

    Returns True if count >= threshold, False otherwise.
    Exits with code 1 if the check fails.
    """
    count = count_unique_entries(parquet_path)

    logger.info(f"Unique 2D material entries found: {count} (Threshold: {threshold})")

    if count < threshold:
        error_msg = f"SC-001 Violation: Pipeline failed to ingest >{threshold} entries. Current count: {count}."
        logger.critical(error_msg)
        logger.critical("Do NOT proceed to training if this check fails.")
        sys.exit(1)

    logger.info("SC-001 Volume Constraint PASSED.")
    return True

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify volume constraint for 2D material dataset (SC-001)."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/graphs_v1.parquet",
        help="Path to the processed graphs parquet file."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=1000,
        help="Minimum number of unique entries required."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    threshold = args.threshold

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.critical(f"SC-001 Violation: Input file missing. Cannot verify volume.")
        sys.exit(1)

    verify_volume_constraint(input_path, threshold)

if __name__ == "__main__":
    main()
