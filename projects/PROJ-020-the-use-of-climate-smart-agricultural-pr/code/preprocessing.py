"""
Preprocessing script to run the sampling pipeline.
"""
import logging
import sys
from pathlib import Path
from data.clean import run_sampling_pipeline
from utils.config import get_raw_data_dir, get_processed_data_dir, get_state_dir
from utils.logging import initialize_logging

def main():
    """Run the preprocessing pipeline."""
    # Initialize logging
    logger = initialize_logging()
    logger.log_operation("preprocessing_start")

    # Run the sampling pipeline
    logger.info("Running sampling pipeline...")
    run_sampling_pipeline()

    logger.log_operation("preprocessing_complete")
    print("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()
