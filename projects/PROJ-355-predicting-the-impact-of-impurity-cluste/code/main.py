import logging
import sys
from pathlib import Path
from typing import Optional
from data.download import main as download_main
from data.gb_builder import main as gb_builder_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline():
    """
    Runs the main pipeline orchestration.
    """
    logger.info("Starting pipeline...")
    # Placeholder for actual pipeline logic
    # This would call download_main, gb_builder_main, etc.
    logger.info("Pipeline completed.")

def main():
    """
    Main entry point for the pipeline script.
    """
    run_pipeline()

if __name__ == "__main__":
    sys.exit(main())
