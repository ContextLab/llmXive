import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import setup_logging, get_logger
from ingestion import main as run_ingestion
from diversity import main as run_diversity
from analysis import main as run_analysis
from viz import main as run_viz
from validation import main as run_validation
from report import main as run_report

logger = get_logger(__name__)

def main():
    """Main pipeline orchestrator."""
    setup_logging()
    logger.info("Starting full analysis pipeline...")

    try:
        # Step 1: Ingestion
        logger.info("Step 1: Running data ingestion...")
        run_ingestion()
        logger.info("Ingestion complete.")

        # Step 2: Diversity Analysis
        logger.info("Step 2: Running diversity analysis...")
        run_diversity()
        logger.info("Diversity analysis complete.")

        # Step 3: Correlation Analysis
        logger.info("Step 3: Running correlation analysis...")
        run_analysis()
        logger.info("Correlation analysis complete.")

        # Step 4: Validation
        logger.info("Step 4: Running validation analysis...")
        run_validation()
        logger.info("Validation complete.")

        # Step 5: Visualization
        logger.info("Step 5: Generating visualizations...")
        run_viz()
        logger.info("Visualizations complete.")

        # Step 6: Report Generation
        logger.info("Step 6: Generating final report...")
        run_report()
        logger.info("Report generation complete.")

        logger.info("Pipeline completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
