"""
Pipeline Runner: Orchestrates the full ingestion pipeline.
"""
import os
import sys
import logging
from pathlib import Path

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from ingestion.cleaner import main as run_cleaner
from ingestion.validator import main as run_validator
from ingestion.citation_tracker import get_tracker
from utils.logging_config import setup_logging, get_logger

logger = get_logger("ingestion.pipeline_runner")

def run_pipeline():
    """
    Execute the full ingestion pipeline: Aggregate -> Clean -> Validate.
    """
    # Initialize logging
    setup_logging()
    logger.info("Starting Ingestion Pipeline.")
    
    # Initialize reproducibility
    init_reproducibility()
    logger.info("Reproducibility initialized.")
    
    tracker = get_tracker()
    tracker.log_operation("pipeline_execution_start", {})
    
    try:
        # Step 1: Aggregate
        logger.info("Step 1: Aggregating data...")
        run_aggregator()
        
        # Step 2: Clean
        logger.info("Step 2: Cleaning data...")
        run_cleaner()
        
        # Step 3: Validate
        logger.info("Step 3: Validating data...")
        run_validator()
        
        tracker.log_operation("pipeline_execution_complete", {"status": "success"})
        logger.info("Ingestion Pipeline completed successfully.")
        
    except Exception as e:
        tracker.log_operation("pipeline_execution_failed", {"error": str(e)})
        logger.error(f"Ingestion Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_pipeline()