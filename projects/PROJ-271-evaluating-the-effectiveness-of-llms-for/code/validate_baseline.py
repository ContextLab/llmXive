import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_data_path, setup_logging


def validate_baseline(csv_path: str) -> bool:
    """
    Validate the static baseline CSV.
    """
    logger = setup_logging(__name__)

    try:
        df = pd.read_csv(csv_path)
        required_columns = ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels"]

        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
            return False

        if len(df) == 0:
            logger.error("Baseline CSV is empty.")
            return False

        logger.info(f"Validation passed. {len(df)} records found.")
        return True

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


def main():
    """Main entry point for baseline validation."""
    csv_path = os.path.join(get_data_path(), "static_baseline.csv")
    if validate_baseline(csv_path):
        print("Baseline validation successful.")
        sys.exit(0)
    else:
        print("Baseline validation failed.")
        sys.exit(1)
