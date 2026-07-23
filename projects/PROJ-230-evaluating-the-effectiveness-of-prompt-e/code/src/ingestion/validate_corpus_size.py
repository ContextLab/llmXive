"""
T014: Validate that the final processed corpus contains at least 200 valid entries.

This script loads the processed corpus from data/processed/corpus.csv and
verifies it meets the minimum size requirement of 200 valid Python-to-JavaScript pairs.
It logs the count and exits with an error if the threshold is not met.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

# Constants
MIN_CORPUS_SIZE = 200
CORPUS_PATH = "data/processed/corpus.csv"
REQUIRED_COLUMNS = ["python_code", "javascript_code"]

def validate_corpus_size(logger: logging.Logger) -> bool:
    """
    Validate that the processed corpus has at least MIN_CORPUS_SIZE entries.

    Args:
        logger: Logger instance for recording validation results.

    Returns:
        True if corpus size >= MIN_CORPUS_SIZE, False otherwise.
    """
    corpus_path = Path(CORPUS_PATH)

    if not corpus_path.exists():
        logger.error(f"Corpus file not found: {corpus_path}")
        return False

    try:
        df = pd.read_csv(corpus_path)
        logger.info(f"Loaded corpus with {len(df)} entries from {corpus_path}")

        # Check required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False

        # Count valid entries (non-null in both code columns)
        valid_mask = df[REQUIRED_COLUMNS].notna().all(axis=1)
        valid_count = valid_mask.sum()
        logger.info(f"Valid entries (non-null python_code and javascript_code): {valid_count}")

        if valid_count < MIN_CORPUS_SIZE:
            logger.error(
                f"Corpus validation FAILED: {valid_count} valid entries < required {MIN_CORPUS_SIZE}"
            )
            return False

        logger.info(
            f"Corpus validation PASSED: {valid_count} valid entries >= {MIN_CORPUS_SIZE}"
        )
        return True

    except pd.errors.EmptyDataError:
        logger.error(f"Corpus file is empty: {corpus_path}")
        return False
    except Exception as e:
        logger.error(f"Error reading corpus: {e}")
        return False

def main():
    """Main entry point for corpus size validation."""
    logger = get_logger("validate_corpus_size")
    logger.info("Starting corpus size validation (T014)")

    success = validate_corpus_size(logger)

    if not success:
        logger.error("Validation failed. Exiting with error code 1.")
        sys.exit(1)

    logger.info("Validation successful. Exiting with code 0.")
    sys.exit(0)

if __name__ == "__main__":
    main()