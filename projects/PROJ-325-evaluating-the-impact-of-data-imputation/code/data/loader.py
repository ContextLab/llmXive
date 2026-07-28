"""
Data Loader for GSS/ACS datasets.
Orchestrates the fetching, validation, and saving of survey data.
"""
import argparse
import logging
import sys
import os
from pathlib import Path
from data_fetcher import fetch_and_save_data, compute_checksum, update_manifest_with_checksum, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the data loader script.
    Parses arguments and triggers the data fetcher.
    """
    parser = argparse.ArgumentParser(description="Load GSS/ACS data for analysis.")
    parser.add_argument("--source", type=str, required=True, choices=["gss", "acs"],
                        help="Data source: 'gss' or 'acs'")
    parser.add_argument("--url", type=str, required=True,
                        help="URL to the dataset (e.g., .dta or .csv)")
    parser.add_argument("--output", type=str, required=True,
                        help="Output path for the processed CSV file")
    parser.add_argument("--cache-dir", type=str, default="data/raw/cache",
                        help="Directory to cache downloaded files")

    args = parser.parse_args()

    # Ensure output directories exist
    output_path = Path(args.output)
    ensure_directories(output_path)
    ensure_directories(Path(args.cache_dir))

    logger.info(f"Starting data fetch for source: {args.source}")
    logger.info(f"Target URL: {args.url}")
    logger.info(f"Output path: {args.output}")

    try:
        # Fetch and save data
        # The fetch_and_save_data function handles the actual download,
        # conversion to CSV, and validation of design columns.
        fetch_and_save_data(
            url=args.url,
            output_path=args.output,
            cache_dir=args.cache_dir,
            source_type=args.source
        )

        # Compute checksum
        checksum = compute_checksum(args.output)
        logger.info(f"Checksum computed: {checksum}")

        # Update manifest
        update_manifest_with_checksum(
            artifact_path=args.output,
            checksum=checksum,
            status="success"
        )

        logger.info(f"Data fetch and validation completed successfully. Output: {args.output}")

    except Exception as e:
        logger.error(f"Data fetch failed: {e}")
        update_manifest_with_checksum(
            artifact_path=args.output,
            checksum="pending",
            status="failed",
            error=str(e)
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
