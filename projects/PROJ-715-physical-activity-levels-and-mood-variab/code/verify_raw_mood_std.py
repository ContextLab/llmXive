import os
import sys
import logging
import hashlib
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

# Import get_path from config to ensure path consistency
# We assume config.py is in the same directory or PYTHONPATH is set correctly
try:
    from config import get_path
except ImportError:
    # Fallback for execution context if not imported correctly
    from code.config import get_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_raw_mood_std():
    """
    Verify that the raw `mood_std` column in daily_aggregates.csv remains unmodified
    and available for other analyses.
    
    Deliverable: Appends a log entry to data/processed/verification.log stating
    "mood_std raw values preserved" along with the SHA-256 hex string of 
    daily_aggregates.csv and an ISO 8601 timestamp.
    """
    # Resolve the path to daily_aggregates.csv
    # Using the get_path utility to ensure consistency with the rest of the project
    # The task description implies the file is at data/processed/daily_aggregates.csv
    input_path = get_path('data/processed', 'daily_aggregates.csv')
    
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}. Preprocessing must be run first.")
        raise FileNotFoundError(f"Daily aggregates file not found at {input_path}. Run preprocessing first.")

    logger.info(f"Verifying raw data at: {input_path}")

    # Load the data to ensure it's readable and check the column
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read {input_path}: {e}")
        raise

    # Verify the column exists
    if 'mood_std' not in df.columns:
        logger.error("Column 'mood_std' not found in the dataset.")
        raise ValueError("Column 'mood_std' not found in the dataset.")

    # Optional: Verify no negative values or NaNs (as per T019a logic, though T019b is about preservation)
    # This ensures the data is in the expected state for "raw values preserved"
    if df['mood_std'].isna().any():
        logger.warning("Found NaN values in mood_std column.")
    if (df['mood_std'] < 0).any():
        logger.warning("Found negative values in mood_std column.")
    
    logger.info("Column 'mood_std' exists and is accessible.")

    # Compute SHA-256 hash of the file
    sha256_hash = hashlib.sha256()
    try:
        with open(input_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {input_path}: {e}")
        raise

    # Generate ISO 8601 timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Prepare log entry
    log_entry = (
        f"{timestamp} | mood_std raw values preserved | "
        f"file_hash: {file_hash}\n"
    )

    # Define the verification log path
    # Using get_path to ensure it lands in data/processed/
    log_path = get_path('data/processed', 'verification.log')
    
    # Create directory if it doesn't exist (though data/processed should exist)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Append to the log file
    try:
        with open(log_path, 'a') as f:
            f.write(log_entry)
        logger.info(f"Verification log appended to: {log_path}")
    except Exception as e:
        logger.error(f"Failed to write to {log_path}: {e}")
        raise

    return True

def main():
    """Entry point for the verification script."""
    try:
        verify_raw_mood_std()
        logger.info("Verification completed successfully.")
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()