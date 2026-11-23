import argparse
import logging
import os
import sys
from pathlib import Path
from config import ensure_directories, dataset_url

# Import runner modules
import run_downloader
import run_build_graphs
import run_metrics
import run_evaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Orchestration script for the full research pipeline.
    Executes: Download -> Parse -> Graph -> Metrics -> Split -> Evaluate.
    """
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    args = parser.parse_args()

    logger.info("Starting llmXive Research Pipeline...")
    
    # Ensure directories exist
    ensure_directories()

    try:
        # Step 1: Download Data
        logger.info("Step 1: Downloading data...")
        run_downloader.main()

        # Step 2: Build Graphs
        logger.info("Step 2: Building graphs...")
        run_build_graphs.main()

        # Step 3: Calculate Metrics
        logger.info("Step 3: Calculating metrics...")
        run_metrics.main()

        # Step 4: Evaluate
        logger.info("Step 4: Running evaluation...")
        run_evaluator.main()

        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
