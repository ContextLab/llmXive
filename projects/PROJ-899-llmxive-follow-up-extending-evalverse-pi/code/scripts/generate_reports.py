"""
Script to generate all reports for the llmXive project.
"""
import os
import sys
import logging
from pathlib import Path

from src.reports.generate import main as reports_main
from src.utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running report generation script...")

    try:
        exit_code = reports_main()
        if exit_code == 0:
            logger.info("Report generation completed successfully.")
        else:
            logger.error("Report generation failed.")
        return exit_code
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
