"""
Task T014: Validate that the final processed corpus contains >= 200 valid entries.

This script loads the processed corpus from data/processed/corpus.csv,
counts the valid entries, and logs the result. It exits with code 0 if
the count is >= 200, otherwise exits with code 1.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = PROJECT_ROOT / "data" / "processed" / "corpus.csv"
MIN_ENTRIES = 200

def validate_corpus_size(corpus_path: Path, min_entries: int = 200) -> bool:
    """
    Load the processed corpus and validate it contains at least min_entries rows.
    
    Args:
        corpus_path: Path to the CSV file containing the processed corpus.
        min_entries: Minimum number of valid entries required.
        
    Returns:
        True if the corpus has >= min_entries, False otherwise.
    """
    if not corpus_path.exists():
        logger.error(f"Corpus file not found at {corpus_path}")
        return False

    try:
        # Load the dataset
        df = pd.read_csv(corpus_path)
        entry_count = len(df)
        
        logger.info(f"Loaded corpus from {corpus_path}")
        logger.info(f"Total entries in corpus: {entry_count}")
        
        # Check against minimum requirement
        if entry_count >= min_entries:
            logger.info(f"SUCCESS: Corpus contains {entry_count} entries (>= {min_entries} required)")
            return True
        else:
            logger.error(f"FAILURE: Corpus contains {entry_count} entries (< {min_entries} required)")
            return False
            
    except Exception as e:
        logger.error(f"Error loading or validating corpus: {e}", exc_info=True)
        return False

def main():
    """Main entry point for the validation script."""
    logger.info(f"Starting corpus size validation for {CORPUS_PATH}")
    
    success = validate_corpus_size(CORPUS_PATH, MIN_ENTRIES)
    
    if success:
        logger.info("Corpus validation passed.")
        sys.exit(0)
    else:
        logger.error("Corpus validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()