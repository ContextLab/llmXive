"""
Main pipeline orchestrator for the Gut Microbiome and Circadian Rhythm study.

This script coordinates the execution of the various pipeline stages:
1. Data ingestion
2. Diversity analysis
3. Correlation analysis
4. Validation
5. Visualization
6. Report generation

Imports of heavy modules (e.g., those requiring optional binary dependencies)
are performed lazily inside the execution flow to avoid import‑time failures
before earlier stages have a chance to run. This ensures that the ingestion
step can create the required `data/processed/cohort_merged.csv` file even
if downstream dependencies (like `biom-format`) are not yet available.
"""
import sys
import logging
from pathlib import Path

# Project root is two levels up from this file (projects/PROJ-037-...)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import setup_logging, get_logger
from ingestion import main as run_ingestion

logger = get_logger(__name__)

def main():
    """Run the full analysis pipeline in the correct order."""
    # Configure root logger
    setup_logging()
    logger.info("Starting full analysis pipeline...")

    try:
        # Step 1: Data Ingestion (must run first to produce cohort_merged.csv)
        logger.info("Step 1: Running data ingestion...")
        run_ingestion()
        logger.info("Ingestion complete.")

        # Verify that the merged cohort file was created
        cohort_path = PROJECT_ROOT / "data" / "processed" / "cohort_merged.csv"
        if not cohort_path.exists():
            raise FileNotFoundError(
                f"Expected merged cohort file not found at {cohort_path}. "
                "The ingestion step should create this file."
            )

        # Lazy imports for the remaining stages (these may depend on optional packages)
        from diversity import main as run_diversity
        from analysis import main as run_analysis
        from validation import main as run_validation
        from viz import main as run_viz
        from report import main as run_report

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