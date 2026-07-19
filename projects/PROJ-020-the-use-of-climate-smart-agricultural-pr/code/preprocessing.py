"""
Preprocessing Pipeline for Climate-Smart Agriculture Data.

This script orchestrates the data cleaning, merging, imputation, and stratified
sampling steps. It is the canonical entry point for the 'preprocessing' stage
referenced in the project run-book.

It performs the following steps:
1. Loads raw data from `data/raw/` (LSMS, NASA POWER, FAOSTAT).
2. Cleans and merges data into a unified dataframe.
3. Applies imputation for missing values.
4. Performs stratified sampling to ensure memory constraints are met.
5. Saves the final processed dataset to `data/processed/merged_sample.parquet`.

Dependencies:
- code/data/clean.py: Contains the core logic for cleaning and sampling.
- code/utils/config.py: Provides configuration for paths and parameters.
"""

import logging
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.clean import run_sampling_pipeline
from utils.config import get_raw_data_dir, get_processed_data_dir, get_state_dir
from utils.logging import initialize_logging

def main():
    """
    Execute the full preprocessing pipeline.
    """
    # Initialize logging
    logger = initialize_logging("preprocessing")
    logger.info("Starting Preprocessing Pipeline (T044)")

    # Ensure directories exist
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    state_dir = get_state_dir()

    for d in [raw_dir, processed_dir, state_dir]:
        d.mkdir(parents=True, exist_ok=True)

    logger.info(f"Raw data directory: {raw_dir}")
    logger.info(f"Processed data directory: {processed_dir}")

    # Check for raw data existence (fail loudly if missing)
    if not raw_dir.exists() or not any(raw_dir.iterdir()):
        logger.error(f"No raw data found in {raw_dir}. Run download pipeline first.")
        raise FileNotFoundError(
            f"Raw data directory {raw_dir} is empty or missing. "
            "Please run the download pipeline (T012-T014) before preprocessing."
        )

    # Run the core pipeline from clean.py
    # This function handles:
    # - Loading raw files
    # - Cleaning and merging
    # - Imputation
    # - Stratified sampling
    # - Saving to parquet
    try:
        output_file = run_sampling_pipeline(
            input_dir=raw_dir,
            output_dir=processed_dir,
            state_dir=state_dir
        )
        
        logger.info(f"Preprocessing complete. Output saved to: {output_file}")
        
        # Verify output file exists and is non-empty
        if not output_file.exists():
            raise FileNotFoundError(f"Output file {output_file} was not created.")
        
        file_size = output_file.stat().st_size
        logger.info(f"Output file size: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError(f"Output file {output_file} is empty.")

    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}", exc_info=True)
        raise

    logger.info("Preprocessing Pipeline (T044) finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())