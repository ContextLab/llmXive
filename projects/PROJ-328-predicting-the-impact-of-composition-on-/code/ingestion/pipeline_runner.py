"""
Pipeline runner for the data ingestion and cleaning phase.

This module orchestrates the sequence of data fetching, scraping,
aggregation, cleaning, and validation to produce the final cleaned dataset.

It ensures that:
1. Raw data is fetched from verified sources (T012a, T012d)
2. Data is aggregated to raw files (T012g)
3. Data is cleaned and filtered (T013)
4. Validation metrics are calculated and status is written (T014)
"""
import os
import sys
import logging
from pathlib import Path
import json
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from ingestion.api_fetcher import main as run_api_fetcher
from ingestion.literature_scraper import main as run_literature_scraper
from ingestion.aggregator import main as run_aggregator
from ingestion.cleaner import main as run_cleaner
from ingestion.validator import main as run_validator
from ingestion.generate_validation_report import main as run_validation_report

logger = get_logger(__name__)

def run_pipeline():
    """
    Execute the full ingestion pipeline.
    
    This function runs the ingestion steps in the correct order:
    1. Fetch data from APIs
    2. Scrape literature
    3. Aggregate to raw files
    4. Clean and filter data
    5. Validate and write status
    """
    logger.info("Starting Ingestion Pipeline...")
    
    # Step 1: Fetch API Data
    logger.info("Step 1: Fetching data from API sources...")
    try:
        run_api_fetcher()
        logger.info("API fetching completed.")
    except Exception as e:
        logger.warning(f"API fetching encountered issues (non-fatal if other sources exist): {e}")
        # We continue because we might have literature data
    
    # Step 2: Scrape Literature
    logger.info("Step 2: Scraping literature sources...")
    try:
        run_literature_scraper()
        logger.info("Literature scraping completed.")
    except Exception as e:
        logger.warning(f"Literature scraping encountered issues: {e}")
        # Continue if we have API data
    
    # Step 3: Aggregate Raw Data
    logger.info("Step 3: Aggregating raw data...")
    try:
        run_aggregator()
        logger.info("Aggregation completed.")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise
    
    # Step 4: Clean Data
    logger.info("Step 4: Cleaning and filtering data...")
    try:
        run_cleaner()
        logger.info("Cleaning completed.")
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        raise
    
    # Step 5: Validate Data and Write Status
    logger.info("Step 5: Validating data and writing status...")
    try:
        run_validator()
        logger.info("Validation completed.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise
        
    # Step 6: Generate Validation Report
    logger.info("Step 6: Generating validation report...")
    try:
        run_validation_report()
        logger.info("Validation report generated.")
    except Exception as e:
        logger.error(f"Validation report generation failed: {e}")
        # Non-fatal for the pipeline, but good to log
        
    logger.info("Ingestion Pipeline completed successfully.")
    return True

def main():
    """
    Main entry point for the pipeline runner.
    """
    try:
        success = run_pipeline()
        if success:
            logger.info("Pipeline execution finished with success.")
            return 0
        else:
            logger.error("Pipeline execution finished with errors.")
            return 1
    except Exception as e:
        logger.critical(f"Pipeline execution crashed: {e}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main())