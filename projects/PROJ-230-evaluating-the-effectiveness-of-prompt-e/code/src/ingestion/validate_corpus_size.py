"""
T014: Validate that the final processed corpus contains >= 200 valid entries.

This script loads the processed corpus CSV and verifies the row count meets
the minimum requirement defined in the project specifications.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger

# Constants
MIN_CORPUS_SIZE = 200
PROCESSED_CORPUS_PATH = "data/processed/corpus.csv"
LOG_FILE = "data/processed/validation_log.txt"

def validate_corpus_size(corpus_path: Path, min_size: int = MIN_CORPUS_SIZE) -> bool:
    """
    Validates that the corpus CSV contains at least min_size entries.
    
    Args:
        corpus_path: Path to the processed corpus CSV file.
        min_size: Minimum required number of entries.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If the corpus file does not exist.
        ValueError: If the file is empty or corrupted.
    """
    logger = get_logger(__name__)
    
    if not corpus_path.exists():
        logger.error(f"Corpus file not found: {corpus_path}")
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
    
    try:
        df = pd.read_csv(corpus_path)
        count = len(df)
        
        logger.info(f"Corpus validation started for: {corpus_path}")
        logger.info(f"Total entries found: {count}")
        logger.info(f"Minimum required entries: {min_size}")
        
        if count < min_size:
            logger.error(f"VALIDATION FAILED: Corpus size ({count}) is below minimum ({min_size})")
            return False
        else:
            logger.info(f"VALIDATION PASSED: Corpus size ({count}) meets minimum requirement ({min_size})")
            return True
            
    except pd.errors.EmptyDataError:
        logger.error(f"Corpus file is empty: {corpus_path}")
        raise ValueError(f"Corpus file is empty: {corpus_path}")
    except Exception as e:
        logger.error(f"Error reading corpus file: {e}")
        raise

def main():
    """Main entry point for corpus size validation."""
    # Setup logging
    logger = get_logger(__name__)
    logger.info("Starting corpus size validation (Task T014)")
    
    corpus_path = project_root / PROCESSED_CORPUS_PATH
    
    try:
        is_valid = validate_corpus_size(corpus_path)
        
        if is_valid:
            logger.info("Task T014 completed successfully: Corpus size is sufficient.")
            return 0
        else:
            logger.error("Task T014 failed: Corpus size is insufficient.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Task T014 failed: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Task T014 failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Task T014 failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())