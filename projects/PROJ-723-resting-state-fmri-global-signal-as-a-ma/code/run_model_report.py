"""
run_model_report.py

Entry point script to execute the model report generation pipeline.
"""

import os
import sys
from pathlib import Path
import logging

from model_report import main
from config import ensure_directories


def main_entry():
    """
    Main entry point for the model report runner.
    """
    # Ensure directories exist
    ensure_directories()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting model report generation...")

    try:
        main()
        logger.info("Model report generation completed successfully.")
    except Exception as e:
        logger.error(f"Model report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_entry()
