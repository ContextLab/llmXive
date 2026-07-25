import os
import sys
import logging
import pandas as pd
from pathlib import Path
from src.utils.logging import get_logger

def validate_corpus_size(corpus_path: str, min_entries: int = 200) -> bool:
    """
    Validates that the processed corpus CSV contains at least `min_entries` valid rows.

    Args:
        corpus_path: Path to the data/processed/corpus.csv file.
        min_entries: Minimum required number of valid entries (default 200).

    Returns:
        True if the count is >= min_entries, False otherwise.

    Raises:
        FileNotFoundError: If the corpus file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    logger = get_logger(__name__)
    path = Path(corpus_path)

    if not path.exists():
        raise FileNotFoundError(f"Corpus file not found at {corpus_path}")

    try:
        df = pd.read_csv(corpus_path)
        count = len(df)
        logger.info(f"Validated corpus size: {count} entries found in {corpus_path}")

        if count < min_entries:
            logger.error(f"Corpus size validation FAILED: {count} < {min_entries} required.")
            return False
        
        logger.info(f"Corpus size validation PASSED: {count} >= {min_entries} required.")
        return True

    except pd.errors.EmptyDataError:
        logger.error(f"Corpus file {corpus_path} is empty.")
        raise ValueError(f"Corpus file {corpus_path} is empty.")
    except Exception as e:
        logger.error(f"Error reading corpus file {corpus_path}: {e}")
        raise

def main():
    """
    Entry point for validating the corpus size.
    Expects the corpus to be at data/processed/corpus.csv.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent.parent
    corpus_path = project_root / "data" / "processed" / "corpus.csv"

    if not corpus_path.exists():
        logger.error(f"Corpus file not found at {corpus_path}. Ensure T013c has run successfully.")
        sys.exit(1)

    try:
        is_valid = validate_corpus_size(str(corpus_path), min_entries=200)
        if not is_valid:
            logger.error("Validation failed: Corpus does not meet the minimum size requirement.")
            sys.exit(1)
        else:
            logger.info("Validation successful: Corpus meets minimum size requirement.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Validation process failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()