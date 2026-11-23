"""
T010b: ATTEMPT REAL DATA FETCH
Runs the ingestion logic to fetch real data.
If successful: Saves raw dataset to data/raw/raw_dataset.csv and validates schema.
If failed: Raises RealDataFetchFailed exception.
"""
import os
import sys
import json
import logging
from pathlib import Path

import pandas as pd

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import setup_logging, log_info, log_error
from config import get_config, ensure_dirs
from ingestion.fetcher import fetch_data, DataFetchError
from ingestion.validator import validate_schema

# Define custom exception for T010b
class RealDataFetchFailed(Exception):
    """Raised when real data fetch fails."""
    pass

logger = logging.getLogger(__name__)

def main():
    """Execute T010b: Attempt real data fetch and validate schema."""
    setup_logging()
    config = get_config()
    ensure_dirs()

    log_info("Starting T010b: Attempting real data fetch...")

    try:
        # Attempt to fetch real data
        df, source, simulation_mode = fetch_data()

        # If simulation_mode is True, real fetch failed (per T010c logic)
        if simulation_mode:
            log_error("Real data fetch failed. Simulation mode triggered.")
            raise RealDataFetchFailed("Real data fetch failed. Simulation mode would be triggered by T010c.")

        if df is None or df.empty:
            log_error("Fetched data is empty.")
            raise RealDataFetchFailed("Fetched data is empty.")

        # Save raw dataset
        raw_path = Path(config['data_raw_dir']) / 'raw_dataset.csv'
        df.to_csv(raw_path, index=False)
        log_info(f"Raw dataset saved to {raw_path}")

        # Validate schema contains required columns
        required_columns = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            error_msg = f"Schema validation failed. Missing columns: {missing_columns}"
            log_error(error_msg)
            raise RealDataFetchFailed(error_msg)

        log_info(f"Schema validation passed. Found columns: {list(df.columns)}")
        log_info(f"Record count: {len(df)}")
        log_info("T010b completed successfully.")

    except DataFetchError as e:
        log_error(f"Data fetch error: {e}")
        raise RealDataFetchFailed(f"Real data fetch failed: {e}")
    except Exception as e:
        log_error(f"Unexpected error during T010b: {e}")
        raise RealDataFetchFailed(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()