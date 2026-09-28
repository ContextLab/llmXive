import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging, get_logger
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main
from analysis.models import main as models_main
from analysis.sensitivity import main as sensitivity_main
from analysis.results import main as results_main
from analysis.bootstrap_ci import main as bootstrap_main
from analysis.fdr_correction import main as fdr_main
from analysis.save_regression_results import main as save_regression_main
from analysis.save_sensitivity_results import main as save_sensitivity_main
from analysis.validation import main as validation_main

def run_pipeline(logger: Optional[logging.Logger] = None):
    """Orchestrate modular steps: Ingestion -> Preprocessing -> Validation -> Modeling -> Sensitivity -> Reporting."""
    if logger is None:
        logger = get_logger("main_pipeline")

    logger.info("Starting pipeline execution.")
    start_time = time.time()

    try:
        # 1. Ingestion
        logger.info("Step 1: Ingestion")
        ingestion_main()

        # 2. Preprocessing
        logger.info("Step 2: Preprocessing")
        preprocessing_main()

        # 3. Cohort Construction & Validation
        logger.info("Step 3: Cohort Construction & Validation")
        validation_main()
        cohort_main()

        # 4. Modeling
        logger.info("Step 4: Modeling")
        models_main()

        # 5. Bootstrap & FDR
        logger.info("Step 5: Bootstrap & FDR")
        bootstrap_main()
        fdr_main()
        save_regression_main()

        # 6. Sensitivity Analysis
        logger.info("Step 6: Sensitivity Analysis")
        sensitivity_main()
        save_sensitivity_main()

        # 7. Reporting
        logger.info("Step 7: Reporting")
        results_main()

        end_time = time.time()
        logger.info(f"Pipeline completed successfully in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise

def main():
    setup_logging()
    logger = get_logger("main_pipeline")
    run_pipeline(logger)

if __name__ == "__main__":
    main()
