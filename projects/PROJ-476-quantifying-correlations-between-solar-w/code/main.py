"""
Main entry point for the Solar Wind - Geomagnetic Correlation Pipeline.

Orchestrates User Story 1 (US1): Data Acquisition & Synchronisation.
Steps:
1. Fetch raw ACE and NOAA data.
2. Validate headers and columns.
3. Align data to 1-hour UTC grid.
4. Interpolate gaps.
5. Save synchronized dataset.
"""
import os
import sys
import argparse
from datetime import datetime

# Ensure code/ is in path for imports if run as script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END, ACE_VARS, NOAA_VARS
from code import logger
from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_columns, validate_ace_headers
from code.data.align import run_alignment

def main():
    """
    Orchestrates the US1 pipeline: download -> validate -> sync.
    """
    parser = argparse.ArgumentParser(description="Run US1: Data Acquisition & Synchronization")
    parser.add_argument(
        "--start",
        type=int,
        default=TRAIN_START,
        help=f"Start year (default: {TRAIN_START})"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=TRAIN_END,
        help=f"End year (default: {TRAIN_END})"
    )
    args = parser.parse_args()

    start_year = args.start
    end_year = args.end

    logger.info(f"Starting US1 Pipeline for period: {start_year} to {end_year}")

    # 1. Fetch Data
    # Define date ranges for fetching
    # We fetch full years to ensure continuous data, then slice if needed later,
    # but fetch.py expects start/end dates.
    fetch_start = datetime(start_year, 1, 1)
    fetch_end = datetime(end_year, 12, 31)

    logger.info(f"Fetching ACE data from {fetch_start} to {fetch_end}...")
    try:
        ace_path = fetch_ace(fetch_start, fetch_end)
        logger.info(f"ACE data fetched: {ace_path}")
    except Exception as e:
        logger.error(f"Failed to fetch ACE data: {e}")
        raise

    logger.info(f"Fetching NOAA data from {fetch_start} to {fetch_end}...")
    try:
        noaa_path = fetch_noaa(fetch_start, fetch_end)
        logger.info(f"NOAA data fetched: {noaa_path}")
    except Exception as e:
        logger.error(f"Failed to fetch NOAA data: {e}")
        raise

    # 2. Validate Data
    # Validate ACE headers specifically as per T012 requirements
    logger.info("Validating ACE data headers...")
    try:
        validate_ace_headers(ace_path)
        logger.info("ACE headers validated successfully.")
    except ValueError as e:
        logger.error(f"ACE validation failed: {e}")
        raise

    # Validate columns for both datasets (generic check)
    # We assume the raw files are loaded into pandas DataFrames for this check
    # inside the align step or here. Since validate.py has validate_columns,
    # we can call it after loading or rely on run_alignment to handle validation.
    # T012 implies abort if missing. Let's do a quick load and check here to be safe.
    import pandas as pd
    df_ace = pd.read_csv(ace_path)
    df_noaa = pd.read_csv(noaa_path)
    
    # Check required ACE vars
    missing_ace = [v for v in ACE_VARS if v not in df_ace.columns]
    if missing_ace:
        err_msg = f"Missing required ACE variables: {missing_ace}"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Check required NOAA vars
    missing_noaa = [v for v in NOAA_VARS if v not in df_noaa.columns]
    if missing_noaa:
        err_msg = f"Missing required NOAA variables: {missing_noaa}"
        logger.error(err_msg)
        raise ValueError(err_msg)

    logger.info("Data validation passed.")

    # 3. Align and Sync
    # This step handles loading, resampling, merging, and interpolation
    logger.info("Running alignment and synchronization...")
    output_path = run_alignment(
        ace_path=ace_path,
        noaa_path=noaa_path,
        output_path="data/processed/synced.csv"
    )
    
    logger.info(f"Pipeline complete. Output saved to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())