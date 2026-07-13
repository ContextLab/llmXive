"""
Pipeline Runner: Orchestrates the full ingestion pipeline.
"""
import os
import sys
import logging
from pathlib import Path

from seed import init_reproducibility
from ingestion.aggregator import LiteratureAggregator, main as run_aggregator
from ingestion.cleaner import DataCleaner, main as run_cleaner
from ingestion.validator import DataValidator, main as run_validator
from ingestion.saver import main as run_saver
from utils.logging_config import get_logger
from config import get_data_raw_dir, get_data_processed_dir

logger = get_logger(__name__)


def run_pipeline():
    """
    Runs the full ingestion pipeline: Aggregate -> Clean -> Validate -> Save.
    """
    init_reproducibility()
    logger.info("Starting Ingestion Pipeline...")

    # 1. Aggregate
    logger.info("Step 1: Aggregating data...")
    run_aggregator()

    # 2. Clean
    logger.info("Step 2: Cleaning data...")
    run_cleaner()

    # 3. Validate
    logger.info("Step 3: Validating data...")
    run_validator()

    # 4. Save (Checksums)
    logger.info("Step 4: Saving with checksums...")
    # The saver logic is integrated into the other steps for simplicity,
    # but this step ensures final checksums are calculated if needed.
    run_saver()

    logger.info("Ingestion Pipeline completed.")

if __name__ == "__main__":
    run_pipeline()
