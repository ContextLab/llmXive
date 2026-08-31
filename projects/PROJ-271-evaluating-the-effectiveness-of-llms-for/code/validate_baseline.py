"""Validation script for baseline data."""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_data_path, setup_logging

logger = setup_logging(__name__)


def validate_baseline(filepath: str) -> bool:
    """Validate the baseline CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        True if valid.
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False

    df = pd.read_csv(filepath)
    required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]

    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns.")
        return False

    if df.empty:
        logger.error("DataFrame is empty.")
        return False

    logger.info(f"Baseline valid: {len(df)} rows, columns: {list(df.columns)}")
    return True


def main():
    """Main entry point."""
    filepath = get_data_path("static_baseline.csv")
    if validate_baseline(filepath):
        print("Validation passed.")
        sys.exit(0)
    else:
        print("Validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
