import os
import sys
import json
import time
import argparse
from typing import Optional, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from config import get_config
from data.ingestion import fetch_all_satellites, verify_data_availability, DataUnavailableError
from data.preprocessing import preprocess_slr_data
from data.output import run_output_pipeline
from utils.logging import get_logger, handle_fatal_error, log_progress

logger = get_logger(__name__)

def main():
    """
    Main entry point for the SLR Equivalence Principle Testing pipeline.
    Orchestrates data ingestion, preprocessing, and output generation.
    """
    parser = argparse.ArgumentParser(description="Run SLR Equivalence Principle Pipeline")
    parser.add_argument("--raw-data-dir", type=str, default="data/raw", help="Directory for raw data")
    parser.add_argument("--processed-data-dir", type=str, default="data/processed", help="Directory for processed data")
    parser.add_argument("--results-dir", type=str, default="data/results", help="Directory for results")
    args = parser.parse_args()

    logger.info("Starting Equivalence Principle Testing Pipeline")
    start_time = time.time()

    try:
        # 1. Load Configuration
        config = get_config()
        raw_data_dir = args.raw_data_dir
        processed_data_dir = args.processed_data_dir
        results_dir = args.results_dir

        # Ensure directories exist
        os.makedirs(raw_data_dir, exist_ok=True)
        os.makedirs(processed_data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)

        # 2. Verify Data Availability
        log_progress(logger, "Verifying data availability...")
        try:
            verify_data_availability(config)
        except DataUnavailableError as e:
            logger.error(str(e))
            # In a real scenario, we might attempt to fetch here if not hardcoded,
            # but T009 logic implies we rely on config verification.
            # If URLs are missing, we cannot proceed.
            return 1

        # 3. Ingest Data
        log_progress(logger, "Fetching satellite data...")
        # The ingestion function handles fetching and basic parsing
        # We assume fetch_all_satellites returns a raw DataFrame
        raw_df = fetch_all_satellites(config.satellite_ids)
        
        if raw_df is None or raw_df.empty:
            logger.error("No data retrieved from ingestion.")
            return 1

        # 4. Preprocess Data
        log_progress(logger, "Preprocessing data (filtering, alignment)...")
        cleaned_df = preprocess_slr_data(raw_df)

        if cleaned_df is None or cleaned_df.empty:
            logger.error("No data remaining after preprocessing.")
            return 1

        # 5. Write Output and Checksums (T019)
        output_csv_path = os.path.join(processed_data_dir, "cleaned_slr_data.csv")
        checksum_dir = processed_data_dir
        
        log_progress(logger, "Saving output and computing checksums...")
        run_output_pipeline(
            cleaned_df=cleaned_df,
            raw_data_dir=raw_data_dir,
            output_csv_path=output_csv_path,
            checksum_dir=checksum_dir
        )

        # 6. Final Report
        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds.")
        logger.info(f"Output saved to: {output_csv_path}")
        
        # Verify checksum file exists
        checksum_file = os.path.join(checksum_dir, ".checksums.json")
        if os.path.exists(checksum_file):
            with open(checksum_file, 'r') as f:
                checksums = json.load(f)
            logger.info(f"Checksums recorded: {checksums}")

        return 0

    except Exception as e:
        handle_fatal_error(logger, e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
