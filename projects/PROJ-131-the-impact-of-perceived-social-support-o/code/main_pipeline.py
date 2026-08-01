"""
Main Pipeline Entry Point for PROJ-131: Social Support & Resilience Analysis.

Orchestrates the full research pipeline: Ingestion -> Preprocessing -> Cohort -> Modeling -> Sensitivity -> Reporting.
Strictly follows the 'Revised Approach' (Single-Dataset Analysis).
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Configure logging
log_dir = Path("data/results")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "pipeline_run.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main_pipeline")

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

def run_pipeline():
    """
    Executes the full research pipeline in sequential order.
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("STARTING MAIN PIPELINE: Social Support & Resilience Analysis")
    logger.info("=" * 60)

    try:
        # Step 1: Ingestion
        logger.info("Step 1: Ingesting Cyberbullying Survey 2021 dataset...")
        from data.ingestion import main as ingestion_main
        ingestion_main()
        logger.info("Step 1 Complete: Ingestion finished.")

        # Step 2: Preprocessing
        logger.info("Step 2: Preprocessing data (MICE, scaling, cleaning)...")
        from data.preprocessing import main as preprocessing_main
        preprocessing_main()
        logger.info("Step 2 Complete: Preprocessing finished.")

        # Step 3: Cohort Construction & Validation
        logger.info("Step 3: Building and validating analysis cohort...")
        from data.cohort import main as cohort_main
        cohort_main()
        logger.info("Step 3 Complete: Cohort validation finished.")

        # Step 4: Modeling (OLS + Bootstrap)
        logger.info("Step 4: Fitting OLS models with interaction terms and bootstrapping...")
        from analysis.models import main as models_main
        models_main()
        logger.info("Step 4 Complete: Modeling finished.")

        # Step 5: Sensitivity Analysis
        logger.info("Step 5: Running sensitivity analysis (continuous harassment, stratification)...")
        from analysis.sensitivity import main as sensitivity_main
        sensitivity_main()
        logger.info("Step 5 Complete: Sensitivity analysis finished.")

        # Step 6: Comparison & Results Saving
        logger.info("Step 6: Comparing sensitivity results with baseline...")
        from analysis.sensitivity_compare import main as compare_main
        compare_main()
        logger.info("Step 6 Complete: Comparison finished.")

        # Step 7: Report Generation
        logger.info("Step 7: Generating markdown summary report...")
        from analysis.results import main as results_main
        results_main()
        logger.info("Step 7 Complete: Report generation finished.")

        end_time = time.time()
        duration = end_time - start_time
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY in {duration:.2f} seconds.")
        logger.info("=" * 60)
        return True

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Check that all modules are present in the 'code/' directory.")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise

def main():
    """
    Entry point for the script.
    """
    try:
        run_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline execution aborted: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()