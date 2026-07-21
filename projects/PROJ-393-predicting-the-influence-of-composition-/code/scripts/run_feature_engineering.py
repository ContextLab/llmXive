"""
Script to run the feature engineering pipeline.
"""

import logging
import sys
from pathlib import Path
from src.features.feature_engineering_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Entry point for the feature engineering script."""
    # Setup logging
    logger = setup_logging(__name__)
    logger.info("Starting Feature Engineering Pipeline via script...")

    try:
        run_pipeline()
        logger.info("Feature Engineering Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Feature Engineering Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()