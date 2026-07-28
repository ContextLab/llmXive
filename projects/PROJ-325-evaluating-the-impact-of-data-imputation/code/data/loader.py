"""
Unified Data Loader for GSS and ACS datasets.

This module provides a CLI interface to fetch and save survey data.
It serves as the reconciled entry point invoked by the run-book (quickstart.md).

It wraps the existing `data_fetcher` logic to support the specific CLI arguments
expected by the run-book: --source, --url, --output.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Import the existing implementation from code/data_fetcher.py
# This ensures we use the verified URL fetcher and checksum logic defined in T004/T004b
from data_fetcher import fetch_and_save_data, compute_checksum, update_manifest_with_checksum, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    CLI entry point for loading GSS or ACS data.
    
    Usage:
    python code/data/loader.py --source "gss" --url "<URL>" --output "data/raw/gss_2018.parquet"
    """
    parser = argparse.ArgumentParser(
        description="Unified loader for survey data (GSS/ACS)."
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["gss", "acs"],
        help="Data source identifier ('gss' or 'acs')."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the dataset file (CSV/Parquet)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Local file path where the data should be saved."
    )

    args = parser.parse_args()

    # Validate output directory
    output_path = Path(args.output)
    ensure_directories(output_path)

    logger.info(f"Fetching data from {args.url} for source '{args.source}'...")
    logger.info(f"Saving to {args.output}")

    try:
        # Fetch and save using the existing verified logic
        # Note: fetch_and_save_data expects the URL and local path
        fetch_and_save_data(args.url, str(output_path))
        
        # Compute checksum
        checksum = compute_checksum(str(output_path))
        logger.info(f"Checksum computed: {checksum}")

        # Update manifest
        manifest_path = Path("state/manifest.yaml")
        update_manifest_with_checksum(
            manifest_path, 
            output_path.name, 
            checksum
        )

        logger.info("Data loading and verification successful.")
        return 0

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        # Fail loudly as per constraints
        return 1

if __name__ == "__main__":
    sys.exit(main())
