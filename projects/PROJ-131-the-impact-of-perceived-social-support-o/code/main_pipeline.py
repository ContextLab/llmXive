import os
import sys
import logging
from pathlib import Path
from typing import Optional
from logger import get_logger

from data.ingestion import main as ingestion_main


def run_pipeline():
    """Run the entire pipeline."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        ingestion_main() # Run ingestion
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


def main():
  run_pipeline()
