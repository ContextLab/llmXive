import os
import sys
import json
import time
import argparse
from typing import Optional, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from data.ingestion import fetch_all_satellites, verify_data_availability
from data.preprocessing import preprocess_slr_data
from data.output import run_output_pipeline
from utils.logging import get_logger, init_logging, log_progress

logger = get_logger(__name__)

def main():
    """
    Main entry point for the SLR Equivalence Principle Pipeline.
    Orchestrates ingestion, preprocessing, and output generation.
    """
    parser = argparse.ArgumentParser(description="SLR Equivalence Principle Pipeline")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--raw-dir', type=str, default='data/raw', help='Path to raw data directory')
    parser.add_argument('--processed-dir', type=str, default='data/processed', help='Path to processed data directory')
    args = parser.parse_args()

    init_logging()
    log_progress("Starting Equivalence Principle Pipeline")

    # 1. Load Configuration
    try:
        config = get_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # 2. Verify Data Availability
    # This checks if the config has the required URLs defined
    if not verify_data_availability(config):
        logger.error("Data URLs not configured. Please update config.yaml with verified_dataset_urls.")
        sys.exit(1)

    # 3. Ingest Data
    # Fetch data for all configured satellites
    # Note: In a real run, this fetches from ILRS. 
    # If data is already in data/raw, this step might skip or validate.
    # For this implementation, we assume fetch_all_satellites handles the download/parsing.
    log_progress("Fetching satellite data...")
    
    # We simulate the ingestion result here if the real fetch is blocked by network,
    # but the function `fetch_all_satellites` is designed to hit the real URLs.
    # To satisfy the "real data" constraint, we call the real function.
    # If it fails, it fails loudly as per constraints.
    try:
        raw_df = fetch_all_satellites(config.satellite_ids)
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        sys.exit(1)

    if raw_df.empty:
        logger.error("Ingested data is empty.")
        sys.exit(1)

    # Save raw data first to ensure preservation
    os.makedirs(args.raw_dir, exist_ok=True)
    raw_csv_path = os.path.join(args.raw_dir, 'raw_slr_points.csv')
    raw_df.to_csv(raw_csv_path, index=False)
    logger.info(f"Saved raw data to {raw_csv_path}")

    # 4. Preprocess Data
    log_progress("Preprocessing data (filtering residuals, time alignment)...")
    try:
        cleaned_df = preprocess_slr_data(raw_df)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    if cleaned_df.empty:
        logger.error("Preprocessed data is empty after filtering.")
        # This might be acceptable if all data was noise, but usually a warning
        logger.warning("All data filtered out. Check residual thresholds.")

    # 5. Output Results
    log_progress("Saving output and computing checksums...")
    output_csv = os.path.join(args.processed_dir, 'cleaned_slr_data.csv')
    checksum_json = os.path.join(args.processed_dir, '.checksums.json')
    
    os.makedirs(args.processed_dir, exist_ok=True)
    
    try:
        run_output_pipeline(
            cleaned_df=cleaned_df,
            raw_data_dir=args.raw_dir,
            output_csv=output_csv,
            checksum_json=checksum_json
        )
    except Exception as e:
        logger.error(f"Output pipeline failed: {e}")
        sys.exit(1)

    log_progress("Pipeline completed successfully.")
    print(f"Output saved to: {output_csv}")
    print(f"Checksums saved to: {checksum_json}")

if __name__ == "__main__":
    main()
