import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Import logging setup from utils if available, otherwise fallback
try:
    from utils import get_logger, setup_logging
except ImportError:
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    def setup_logging():
        pass

def validate_golden_set():
    """
    Validates the existence and integrity of the Golden Set file.
    
    Checks:
    1. File existence at data/processed/golden_set.csv
    2. Minimum row count (>= 50)
    3. Presence of 'expert_load_score' column
    4. Validity of scores (0-100 range, numeric)
    
    Raises:
        SystemExit: If validation fails with the specific error message.
        FileNotFoundError: If the file is missing.
    """
    logger = get_logger(__name__)
    logger.info("Starting Golden Set validation...")
    
    file_path = Path("data/processed/golden_set.csv")
    
    # Check 1: File existence
    if not file_path.exists():
        logger.error("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
        # Raise SystemExit to halt the pipeline cleanly as per spec
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read Golden Set CSV: {e}")
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    # Check 2: Minimum row count
    row_count = len(df)
    logger.info(f"Golden Set contains {row_count} rows.")
    if row_count < 50:
        logger.error(f"Golden Set has only {row_count} rows. Minimum required is 50.")
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    # Check 3: Required column
    if 'expert_load_score' not in df.columns:
        logger.error("Column 'expert_load_score' is missing from the Golden Set.")
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    # Check 4: Validity of scores
    scores = df['expert_load_score']
    
    # Check for non-numeric values
    if not pd.api.types.is_numeric_dtype(scores):
        # Try to convert, if it fails, it's invalid
        try:
            scores = pd.to_numeric(scores, errors='raise')
        except ValueError:
            logger.error("Column 'expert_load_score' contains non-numeric values.")
            sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    # Check range 0-100
    invalid_scores = scores[(scores < 0) | (scores > 100)]
    if len(invalid_scores) > 0:
        logger.error(f"Found {len(invalid_scores)} expert_load_score values outside the valid range [0, 100].")
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    # Check for NaNs
    if scores.isna().any():
        logger.error("Found NaN values in 'expert_load_score' column.")
        sys.exit("Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training.")
    
    logger.info("Golden Set validation PASSED.")
    logger.info(f"  - Rows: {row_count}")
    logger.info(f"  - Score range: [{scores.min()}, {scores.max()}]")
    return True

def main():
    setup_logging()
    validate_golden_set()

if __name__ == "__main__":
    main()
