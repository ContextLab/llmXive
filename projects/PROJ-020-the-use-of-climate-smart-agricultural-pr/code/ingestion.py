"""
Ingestion wrapper script to execute data download and merge logic.
"""
import logging
import sys
from pathlib import Path
from data.download import download_lsms_batch, download_nasa_power_batch, download_faostat_batch
from data.clean import run_sampling_pipeline
from utils.logging import initialize_logging

def main():
    """Run the ingestion pipeline."""
    # Initialize logging
    logger = initialize_logging()
    logger.log_operation("ingestion_start")

    # Download data
    logger.info("Downloading LSMS data...")
    lsms_files = download_lsms_batch()
    logger.info(f"Downloaded {len(lsms_files)} LSMS files")

    logger.info("Downloading NASA POWER data...")
    # Coordinates for target countries
    locations = [
        {"lat": -1.2921, "lon": 36.8219}, # Kenya
        {"lat": 28.6139, "lon": 77.2090}, # India
        {"lat": 21.0285, "lon": 105.8542} # Vietnam
    ]
    nasa_files = download_nasa_power_batch(locations, "2015-01-01", "2021-12-31")
    logger.info(f"Downloaded {len(nasa_files)} NASA POWER files")

    logger.info("Downloading FAOSTAT data...")
    faostat_files = download_faostat_batch(["CROP", "LIVESTOCK", "FORESTRY"])
    logger.info(f"Downloaded {len(faostat_files)} FAOSTAT files")

    # Run cleaning and sampling pipeline
    logger.info("Running sampling pipeline...")
    run_sampling_pipeline()

    logger.log_operation("ingestion_complete")
    print("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
