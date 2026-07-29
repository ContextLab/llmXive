"""
Scaffolding for the literature ingestion pipeline.

This module provides the structural foundation for T005, defining the 
entry point and directory structure for the literature aggregator.
It integrates with the existing aggregator.py to ensure the pipeline
is ready for data fetching and processing.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from ingestion.cleaner import main as run_cleaner
from ingestion.validator import main as run_validator
from ingestion.saver import main as run_saver
from ingestion.citation_tracker import get_tracker, reset_tracker
from config import get_data_raw_dir, get_data_processed_dir, get_log_level, get_log_format
from utils.logging_config import setup_logging

def setup_directories():
    """Ensure required data directories exist."""
    raw_dir = get_data_raw_dir()
    processed_dir = get_data_processed_dir()
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Ensured directories exist: {raw_dir}, {processed_dir}")

def main():
    """
    Main entry point for the ingestion pipeline scaffold.
    
    This function orchestrates the ingestion process:
    1. Initializes reproducibility seeds.
    2. Sets up logging and directory structure.
    3. Runs the literature aggregator to fetch raw data.
    4. Runs the cleaner to standardize data.
    5. Runs the validator to check data integrity.
    6. Saves the validated dataset with checksums.
    """
    # Initialize reproducibility
    init_reproducibility()
    
    # Setup logging
    log_level = get_log_level()
    log_format = get_log_format()
    logger = setup_logging(level=log_level, format_str=log_format)
    logger.info("Starting Ingestion Pipeline Scaffold (T005)")
    
    try:
        # 1. Setup directories
        setup_directories()
        
        # 2. Reset citation tracker
        reset_tracker()
        
        # 3. Run Aggregator
        logger.info("Step 1: Running Literature Aggregator...")
        raw_data_path = run_aggregator()
        if not raw_data_path:
            logger.error("Aggregator failed to produce raw data.")
            return False
        
        # 4. Run Cleaner
        logger.info("Step 2: Running Data Cleaner...")
        cleaned_data_path = run_cleaner(raw_data_path)
        if not cleaned_data_path:
            logger.error("Cleaner failed to produce cleaned data.")
            return False
        
        # 5. Run Validator
        logger.info("Step 3: Running Data Validator...")
        validated_data_path = run_validator(cleaned_data_path)
        if not validated_data_path:
            logger.error("Validator failed to produce validated data.")
            return False
        
        # 6. Save with checksums
        logger.info("Step 4: Saving Validated Data with Checksums...")
        success = run_saver(validated_data_path)
        if not success:
            logger.error("Saver failed to save data.")
            return False
        
        logger.info("Ingestion Pipeline completed successfully.")
        return True
        
    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
