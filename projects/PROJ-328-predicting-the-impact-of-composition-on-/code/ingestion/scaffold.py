"""
Ingestion Scaffolding Module

This module provides the directory structure setup and orchestration
for the literature data ingestion pipeline. It initializes the necessary
folders for raw and processed data and prepares the environment for
the LiteratureAggregator to fetch data from verified sources.
"""

import os
import sys
import logging
from pathlib import Path

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from utils.logging_config import get_logger
from config import get_data_raw_dir, get_data_processed_dir, get_data_outputs_dir

# Initialize logger for this module
logger = get_logger(__name__)


def setup_directories() -> dict:
    """
    Creates the required directory structure for the ingestion pipeline.
    Ensures that raw, processed, and output directories exist.

    Returns:
        dict: A dictionary containing the paths to the created directories.
    """
    init_reproducibility()

    directories = {
        'raw': get_data_raw_dir(),
        'processed': get_data_processed_dir(),
        'outputs': get_data_outputs_dir()
    }

    for name, path in directories.items():
        if not path.exists():
            logger.info(f"Creating directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
        else:
            logger.debug(f"Directory already exists: {path}")

    logger.info("Ingestion directory scaffolding complete.")
    return directories


def main():
    """
    Main entry point for the ingestion scaffolding task.
    Sets up directories and runs the literature aggregator if configured.
    """
    init_reproducibility()
    
    logger.info("Starting ingestion scaffolding task (T005).")
    
    # Step 1: Setup directory structure
    dirs = setup_directories()
    
    # Step 2: Run the aggregator (this is where the real data ingestion happens)
    # The aggregator is responsible for fetching real data from the 
    # 'Verified Literature Corpus' and other sources as defined in aggregator.py
    logger.info("Executing LiteratureAggregator...")
    run_aggregator()
    
    logger.info("Ingestion scaffolding task completed successfully.")


if __name__ == "__main__":
    main()