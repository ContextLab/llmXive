"""Volume constraint verification for the ingestion pipeline.

This module implements SC-001: Verify that the pipeline ingests >1,000
unique 2D material entries. If the count is below the threshold, the
pipeline must exit with code 1 and log a critical error.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Threshold defined in SC-001
VOLUME_THRESHOLD = 1000

logger = logging.getLogger(__name__)


def count_unique_entries(parquet_path: Path) -> int:
    """Count unique 2D material entries in a Parquet file.

    Args:
        parquet_path: Path to the Parquet file containing the ingested data.

    Returns:
        The number of unique entries (rows) in the dataset.

    Raises:
        FileNotFoundError: If the Parquet file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        raise ValueError(f"Failed to read Parquet file: {e}")

    if df.empty:
        logger.warning("Parquet file is empty.")
        return 0

    # Count unique entries based on the number of rows
    # Assuming each row represents a unique material entry
    unique_count = len(df)
    logger.info(f"Found {unique_count} unique entries in {parquet_path.name}")

    return unique_count


def verify_volume_constraint(parquet_path: Path, threshold: int = VOLUME_THRESHOLD) -> bool:
    """Verify that the dataset meets the minimum volume constraint.

    Args:
        parquet_path: Path to the Parquet file containing the ingested data.
        threshold: Minimum number of unique entries required (default: 1000).

    Returns:
        True if the constraint is satisfied, False otherwise.

    Raises:
        SystemExit: If the constraint is NOT satisfied (exits with code 1).
    """
    try:
        count = count_unique_entries(parquet_path)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Failed to count entries: {e}")
        sys.exit(1)

    if count < threshold:
        error_msg = f"SC-001 Violation: Pipeline failed to ingest >{threshold} entries. Current count: {count}."
        logger.critical(error_msg)
        # Exit with code 1 to halt the pipeline
        sys.exit(1)

    logger.info(f"Volume constraint satisfied: {count} entries >= {threshold} threshold.")
    return True


def main() -> None:
    """CLI entry point for volume constraint verification."""
    parser = argparse.ArgumentParser(
        description="Verify that the ingestion pipeline meets the volume constraint (SC-001)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the output Parquet file (e.g., data/processed/graphs_v1.parquet).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=VOLUME_THRESHOLD,
        help=f"Minimum number of unique entries required (default: {VOLUME_THRESHOLD}).",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting volume constraint verification...")
    verify_volume_constraint(args.input, args.threshold)
    logger.info("Volume constraint verification completed successfully.")


if __name__ == "__main__":
    main()
