"""
Script to execute the fetching logic from T018 (via fetch_era5_full.py)
and merge the resulting ERA5 data with the Moral Machine dataset.

This task (T018b) depends on:
- T018: Implementation of fetching logic in code/ingestion.py
- T002d: Availability of the full ERA5 dataset in data/raw/era5_full.h5

It performs:
1. Loads the pre-fetched full ERA5 dataset (data/raw/era5_full.h5)
2. Loads the Moral Machine dataset via code/ingestion.py
3. Applies geospatial matching and temperature interpolation
4. Saves the merged output to data/processed/merged_dataset.parquet
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from ingestion import (
    load_moral_machine_dataset,
    filter_invalid_records,
    fetch_era5_temperature,
    add_era5_temperature_to_df,
    match_geospatial_records,
    interpolate_missing_temperature,
    generate_merged_output,
    ensure_exclusion_log_exists,
    log_excluded_records
)

def main():
    """
    Main entry point for T018b: Merge ERA5 and Moral Machine data.
    """
    # Setup logging
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T018b: Merge ERA5 and Moral Machine data.")

    # Define paths
    era5_full_path = project_root / "data" / "raw" / "era5_full.h5"
    moral_machine_path = project_root / "data" / "raw" / "moral_machine.parquet"
    output_path = project_root / "data" / "processed" / "merged_dataset.parquet"
    exclusion_log_path = project_root / "results" / "logs" / "exclusion_log.csv"

    # Verify input files exist
    if not era5_full_path.exists():
        logger.error(f"Full ERA5 dataset not found at {era5_full_path}. "
                     "Please ensure T002c has been executed successfully.")
        sys.exit(1)

    if not moral_machine_path.exists():
        logger.error(f"Moral Machine dataset not found at {moral_machine_path}. "
                     "Please ensure the dataset has been downloaded.")
        sys.exit(1)

    # Ensure exclusion log exists
    ensure_exclusion_log_exists(exclusion_log_path)

    try:
        # Step 1: Load Moral Machine dataset
        logger.info("Loading Moral Machine dataset...")
        moral_df = load_moral_machine_dataset(moral_machine_path)
        logger.info(f"Loaded {len(moral_df)} records from Moral Machine.")

        # Step 2: Filter invalid records
        logger.info("Filtering invalid records...")
        filtered_df, excluded_records = filter_invalid_records(moral_df)
        if excluded_records:
            log_excluded_records(excluded_records, exclusion_log_path, reason="Invalid response time or missing location")
            logger.info(f"Excluded {len(excluded_records)} invalid records.")
        else:
            logger.info("No records excluded during initial filtering.")

        # Step 3: Load ERA5 data
        logger.info("Loading ERA5 temperature data...")
        era5_df = fetch_era5_temperature(era5_full_path)
        logger.info(f"Loaded {len(era5_df)} ERA5 records.")

        # Step 4: Geospatial matching
        logger.info("Performing geospatial matching...")
        matched_df, low_quality_matches = match_geospatial_records(filtered_df, era5_df, max_distance_km=100)
        
        if low_quality_matches:
            log_excluded_records(low_quality_matches, exclusion_log_path, reason="distance > 100km")
            logger.info(f"Excluded {len(low_quality_matches)} records due to distance > 100km.")

        logger.info(f"Matched {len(matched_df)} records geospatially.")

        # Step 5: Add temperature data
        logger.info("Adding temperature data to matched records...")
        temp_df = add_era5_temperature_to_df(matched_df, era5_df)

        # Step 6: Interpolate missing temperatures
        logger.info("Interpolating missing temperature values...")
        final_df, interpolated_excluded = interpolate_missing_temperature(temp_df)
        
        if interpolated_excluded:
            log_excluded_records(interpolated_excluded, exclusion_log_path, reason="temporal_gap > 2h")
            logger.info(f"Excluded {len(interpolated_excluded)} records due to interpolation gaps > 2h.")

        logger.info(f"Final dataset size after interpolation: {len(final_df)} records.")

        # Step 7: Generate output
        logger.info("Saving merged dataset...")
        generate_merged_output(final_df, output_path)
        
        logger.info(f"Successfully saved merged dataset to {output_path}")
        logger.info("T018b completed successfully.")

    except Exception as e:
        logger.error(f"Error during T018b execution: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
