"""
Script entry point to run the Feature Engineering Pipeline (Task T032).

This script executes the pipeline to transform preprocessed alloy data
into a feature-rich dataset ready for model training.

Usage:
    python code/scripts/run_feature_engineering.py
"""

import logging
import sys
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.features.feature_engineering_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Execute the feature engineering pipeline."""
    logger = setup_logging(__name__)
    logger.info("Starting Feature Engineering Script via CLI.")
    try:
        run_pipeline()
        logger.info("Feature Engineering Script completed successfully.")
    except Exception as e:
        logger.error(f"Feature Engineering Script failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()