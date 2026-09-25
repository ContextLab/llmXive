import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

from src.ingestion.agp_loader import fetch_agp_data, main as agp_main
from src.ingestion.ukbb_loader import fetch_ukbb_data, main as ukbb_main
from src.ingestion.harmonizer import harmonize_and_merge, main as harmonizer_main
from src.ingestion.logging_config import get_ingestion_logger, log_download_status, log_filter_counts, log_merge_result
from src.utils.logger import get_logger

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def run_agp_ingestion(logger: logging.Logger) -> bool:
    """
    Executes the AGP data ingestion process.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info("Starting AGP ingestion...")
    try:
        # This function call is expected to perform the download and write to data/raw/agp_raw.tsv
        # It will raise an error if the download fails (per T012 constraints)
        fetch_agp_data() 
        log_download_status(logger, "AGP", "SUCCESS")
        return True
    except Exception as e:
        log_download_status(logger, "AGP", "FAIL", str(e))
        return False

def run_ukbb_ingestion(logger: logging.Logger) -> bool:
    """
    Executes the UKBB data ingestion process.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info("Starting UKBB ingestion...")
    try:
        # This function call is expected to perform the download and write to data/raw/ukbb_raw.tsv
        fetch_ukbb_data()
        log_download_status(logger, "UKBB", "SUCCESS")
        return True
    except Exception as e:
        log_download_status(logger, "UKBB", "FAIL", str(e))
        return False

def run_harmonization(logger: logging.Logger) -> bool:
    """
    Executes the data harmonization and merging process.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info("Starting harmonization and merge...")
    try:
        # harmonize_and_merge performs the filtering, unit conversion, and merging.
        # It returns the final DataFrame and metadata about the process.
        merged_df, stats = harmonize_and_merge()
        
        if merged_df is None:
            logger.error("Harmonization failed: No data returned.")
            return False

        # Log filter counts
        # Assuming stats contains keys like 'filtered_read_count', 'filtered_fiber_range', etc.
        # We log generic counts based on the task requirement "Filtered Samples: <count>"
        total_filtered = 0
        if 'filtered_count' in stats:
            total_filtered = stats['filtered_count']
            log_filter_counts(logger, "General", total_filtered)
        
        # Log harmonization result
        log_merge_result(logger, len(merged_df), stats.get('agp_count', 0), stats.get('ukbb_count', 0))
        
        return True
    except Exception as e:
        logger.error(f"Harmonization failed with error: {e}")
        return False

def main():
    """
    Main entry point for the ingestion pipeline.
    Orchestrates AGP download, UKBB download, and Harmonization.
    """
    parser = argparse.ArgumentParser(description="Run the full ingestion pipeline.")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    # Initialize the ingestion logger
    logger = get_ingestion_logger()
    logger.setLevel(getattr(logging, args.log_level))

    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    success = True

    # 1. Run AGP Ingestion
    if not run_agp_ingestion(logger):
        success = False
        # Depending on strictness, we might stop here. 
        # For logging purposes, we continue to try UKBB but mark overall as failed.

    # 2. Run UKBB Ingestion
    if not run_ukbb_ingestion(logger):
        success = False

    # 3. Run Harmonization
    # Only run if both downloads succeeded, or if we want to try merging partial data.
    # Per T014, we need both to merge. If one failed, harmonization will likely fail or produce empty.
    # We attempt it to ensure the log captures the final state, but it will likely fail loudly.
    if success:
        if not run_harmonization(logger):
            success = False
    else:
        logger.error("Skipping harmonization due to previous ingestion failures.")

    if success:
        logger.info("Ingestion pipeline completed successfully.")
    else:
        logger.error("Ingestion pipeline completed with errors.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
