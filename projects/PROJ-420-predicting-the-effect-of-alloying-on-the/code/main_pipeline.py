"""
Main orchestration script for the Aluminum Alloy Poisson's Ratio prediction pipeline.
This script reconciles the run-book (quickstart.md) with the implementation.
It executes the full pipeline: Data Extraction -> Cleaning -> Modeling -> Analysis -> Report.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import pipeline stages from their respective modules
# Note: Imports are structured to match the existing API surface in the project
from data.download import main as download_main
from data.clean import main as clean_main
from modeling import main as modeling_main
from analysis import main as analysis_main
from main import main as report_main
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    parser = argparse.ArgumentParser(
        description="Run the full Poisson's Ratio prediction pipeline."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip data extraction if raw data already exists.",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip data cleaning if processed data already exists.",
    )
    parser.add_argument(
        "--skip-modeling",
        action="store_true",
        help="Skip model training if model artifact exists.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis if results exist.",
    )
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip final report generation.",
    )
    args = parser.parse_args()

    # Setup logging using the project's tolerant logging config
    logger = setup_logging(level=args.log_level)
    logger.info("Starting main pipeline orchestration.")

    config = get_config()

    try:
        # 1. Data Extraction (T009a, T009b)
        if not args.skip_download:
            logger.info("Step 1: Running Data Extraction...")
            download_main()
        else:
            logger.info("Step 1: Skipping Data Extraction.")

        # 2. Data Cleaning (T010-T016)
        if not args.skip_clean:
            logger.info("Step 2: Running Data Cleaning...")
            clean_main()
        else:
            logger.info("Step 2: Skipping Data Cleaning.")

        # 3. Modeling (T019-T025)
        if not args.skip_modeling:
            logger.info("Step 3: Running Modeling Pipeline...")
            modeling_main()
        else:
            logger.info("Step 3: Skipping Modeling Pipeline.")

        # 4. Analysis (T027a-T029)
        if not args.skip_analysis:
            logger.info("Step 4: Running Analysis Pipeline...")
            analysis_main()
        else:
            logger.info("Step 4: Skipping Analysis Pipeline.")

        # 5. Report Generation (T030a)
        if not args.skip_report:
            logger.info("Step 5: Generating Final Report...")
            report_main()
        else:
            logger.info("Step 5: Skipping Final Report Generation.")

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())