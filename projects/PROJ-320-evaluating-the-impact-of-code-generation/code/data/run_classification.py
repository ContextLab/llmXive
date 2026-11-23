"""
Runner script to execute PR classification and generate the intermediate labeled dataset.
This script ensures that the classification pipeline runs end-to-end and produces the required output.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.classify_prs import run_classification, setup_logging_and_config
from utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """Main entry point for running the classification pipeline."""
    logger.info("Starting PR classification pipeline...")

    # Setup logging and config
    setup_logging_and_config()

    # Run classification
    classified_prs = run_classification()

    if not classified_prs:
        logger.error("Classification failed: no PRs were classified")
        sys.exit(1)

    logger.info(f"Successfully classified {len(classified_prs)} PRs")
    logger.info("Classification pipeline completed successfully")

    return classified_prs

if __name__ == "__main__":
    main()