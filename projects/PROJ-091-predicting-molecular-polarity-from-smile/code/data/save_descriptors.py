"""
T018: Save processed feature matrix to data/processed/descriptors.parquet.

This script orchestrates the final step of User Story 1:
1. Runs the preprocessing pipeline (T014-T017) to generate descriptors.
2. Saves the resulting DataFrame to `data/processed/descriptors.parquet`.
3. Validates the output file exists and is readable.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger, set_log_level
from data.preprocess_2d import preprocess_2d

# Configure logger
logger = get_logger(__name__)
set_log_level(logging.INFO)

def main():
    """
    Main entry point for T018.
    Executes preprocessing and saves the result to the specified Parquet file.
    """
    logger.info("Starting T018: Saving processed descriptors to Parquet.")

    # Define paths
    processed_dir = PROJECT_ROOT / "data" / "processed"
    output_path = processed_dir / "descriptors.parquet"

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Check if raw data exists (dependency on T013)
    raw_dir = PROJECT_ROOT / "data" / "raw"
    qm9_file = raw_dir / "qm9_smiles.csv" # Assuming standard output from T013

    if not qm9_file.exists():
        logger.error(f"Raw data file not found: {qm9_file}. "
                     "Please ensure T013 (download_qm9.py) has been run successfully.")
        sys.exit(1)

    logger.info(f"Processing data from: {qm9_file}")
    logger.info(f"Target output: {output_path}")

    try:
        # Run the full preprocessing pipeline
        # This function handles:
        # - Descriptor computation (T014)
        # - Correlation filtering (T015)
        # - NaN handling (T016)
        # - Batch processing (T017)
        df_processed = preprocess_2d(str(qm9_file))

        if df_processed is None or df_processed.empty:
            logger.error("Preprocessing returned an empty or None DataFrame. Aborting save.")
            sys.exit(1)

        # Validate schema (basic check)
        if 'target' not in df_processed.columns:
            logger.error("Processed DataFrame missing 'target' column.")
            sys.exit(1)

        # Save to Parquet
        # Using index=False to keep it clean, as row order is generally not critical for ML
        logger.info(f"Writing {len(df_processed)} rows to {output_path}...")
        df_processed.to_parquet(str(output_path), index=False, engine='pyarrow')

        # Verify file was written
        if not output_path.exists():
            logger.error("Output file was not created despite no exceptions.")
            sys.exit(1)

        file_size = output_path.stat().st_size
        logger.info(f"Successfully saved descriptors. File size: {file_size / (1024*1024):.2f} MB.")
        logger.info(f"Columns saved: {list(df_processed.columns)}")

        return 0

    except Exception as e:
        logger.error(f"Critical error during T018 execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())