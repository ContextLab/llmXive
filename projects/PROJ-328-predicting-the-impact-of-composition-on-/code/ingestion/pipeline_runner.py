"""
Pipeline runner for the solder hardness ingestion pipeline.
Orchestrates the aggregation, cleaning, validation, and saving steps.
"""
import os
import sys
import logging
from pathlib import Path

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from ingestion.cleaner import DataCleaner, main as run_cleaner
from ingestion.validator import DataValidator, main as run_validator
from ingestion.saver import (
    save_raw_data_with_checksums,
    save_validated_data
)
from config import get_data_raw_dir, get_data_processed_dir, get_min_samples_warning
from utils.logging_config import get_logger

logger = get_logger(__name__)


def run_pipeline() -> None:
    """
    Execute the full ingestion pipeline:
    1. Aggregate data from literature sources
    2. Clean and filter data
    3. Validate data quality
    4. Save raw and validated datasets
    """
    init_reproducibility()
    
    logger.info("Starting Solder Hardness Ingestion Pipeline")
    
    # Step 1: Aggregate
    logger.info("Step 1: Aggregating data from literature sources...")
    raw_data = run_aggregator()
    if not raw_data:
        logger.error("Aggregation failed or returned no data. Aborting pipeline.")
        return
    
    # Step 2: Clean
    logger.info("Step 2: Cleaning and filtering data...")
    cleaned_data = run_cleaner(raw_data)
    if not cleaned_data:
        logger.error("Cleaning failed or returned no data. Aborting pipeline.")
        return
    
    # Step 3: Validate
    logger.info("Step 3: Validating data quality...")
    validated_data, validation_warnings = run_validator(cleaned_data)
    
    if not validated_data:
        logger.error("Validation failed or returned no data. Aborting pipeline.")
        return
    
    sample_count = len(validated_data)
    min_warning = get_min_samples_warning()
    
    if sample_count < min_warning:
        logger.warning(f"Dataset size ({sample_count}) is below the warning threshold ({min_warning}).")
        if 50 <= sample_count < 100:
            logger.warning(f"Dataset size ({sample_count}) is between 50 and 100. Warning emitted as per spec.")
    
    # Step 4: Save
    logger.info("Step 4: Saving datasets...")
    
    raw_dir = get_data_raw_dir()
    processed_dir = get_data_processed_dir()
    
    raw_csv_path = raw_dir / "solder_hardness_raw.csv"
    checksums_path = raw_dir.parent / "checksums.txt"
    validated_csv_path = processed_dir / "solder_hardness_validated.csv"
    
    save_raw_data_with_checksums(cleaned_data, raw_csv_path, checksums_path)
    save_validated_data(validated_data, validated_csv_path)
    
    logger.info("Pipeline completed successfully.")
    logger.info(f"Raw data saved to: {raw_csv_path}")
    logger.info(f"Validated data saved to: {validated_csv_path}")
    logger.info(f"Checksums saved to: {checksums_path}")


def main() -> None:
    """
    Main entry point for running the ingestion pipeline.
    """
    run_pipeline()


if __name__ == "__main__":
    main()