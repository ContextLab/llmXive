import os
import sys
import logging
from pathlib import Path
import json

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from ingestion.cleaner import DataCleaner, main as run_cleaner
from ingestion.validator import DataValidator, main as run_validator
from ingestion.saver import save_validated_data, main as run_saver
from config import get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_pipeline():
    """
    Execute the full ingestion pipeline:
    1. Aggregate (T012)
    2. Clean (T013)
    3. Validate (T014)
    4. Save Validated (T016)
    """
    init_reproducibility()
    
    logger.info("Starting Solder Hardness Ingestion Pipeline")
    
    # Step 1: Aggregate
    # The aggregator returns a list of raw records
    logger.info("Step 1: Aggregating data from sources...")
    try:
        raw_data = run_aggregator()
        if not raw_data:
            logger.error("Aggregation returned no data. Stopping pipeline.")
            return False
        logger.info(f"Aggregated {len(raw_data)} raw records.")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        # Per T012, we might have partial data, but if critical sources fail, we stop
        if "ConfigError" in str(type(e)):
            return False
        # If we have partial data, we might continue, but for T016 we need a valid set
        # We proceed if we have some data, but the validator will handle the count check
        raw_data = [] 
    
    # Step 2: Clean
    logger.info("Step 2: Cleaning data...")
    try:
        cleaned_data = run_cleaner(raw_data)
        logger.info(f"Cleaned data: {len(cleaned_data)} records.")
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        return False
    
    # Step 3: Validate
    logger.info("Step 3: Validating data...")
    try:
        validated_data, validation_status = run_validator(cleaned_data)
        if not validated_data:
            logger.error("Validation returned no data. Stopping pipeline.")
            return False
        
        # Save status for T016b
        status_path = get_data_processed_dir() / ".ingestion_status.json"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        with open(status_path, 'w') as f:
            json.dump(validation_status, f, indent=2)
        
        logger.info(f"Validation complete. Status: {validation_status.get('threshold_status')}")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False
    
    # Step 4: Save Validated (T016)
    logger.info("Step 4: Saving validated dataset (T016)...")
    try:
        output_path = save_validated_data(validated_data)
        logger.info(f"Pipeline complete. Validated data saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Saving validated data failed: {e}")
        return False

def main():
    """Entry point for the pipeline."""
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
