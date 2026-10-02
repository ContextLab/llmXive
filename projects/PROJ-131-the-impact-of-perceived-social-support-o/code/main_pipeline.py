"""
Main Pipeline Entry Point for PROJ-131
Orchestrates the single-dataset analysis of social support and resilience.

This script executes the full pipeline:
1. Ingestion (T012)
2. Preprocessing (T013)
3. Cohort Construction (T014-T016)
4. Modeling (T020-T024)
5. Sensitivity Analysis (T027-T029)
6. Reporting (T025)
"""
import os
import sys
import logging
import time
import traceback
from pathlib import Path

# Ensure project root is in path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logging, get_logger
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main
from analysis.models import main as models_main
from analysis.sensitivity import main as sensitivity_main
from analysis.save_regression_results import main as save_results_main
from analysis.save_sensitivity_results import main as save_sensitivity_main
from analysis.results import main as results_main
from analysis.performance_benchmark import main as benchmark_main

logger = None

def run_pipeline():
    """Execute the full research pipeline."""
    global logger
    
    # 1. Initialize Logging
    log_path = PROJECT_ROOT / "data" / "results"
    log_path.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_file=log_path / "pipeline_run.log")
    logger.info("=" * 80)
    logger.info("Starting Main Pipeline Execution")
    logger.info("=" * 80)

    start_time = time.time()

    try:
        # 2. Data Ingestion (T012)
        # This step downloads/loads the raw data and saves to data/raw/
        logger.info("Step 1: Data Ingestion")
        ingestion_main()
        logger.info("Step 1: Complete")

        # 3. Preprocessing (T013)
        # Imputation, scaling, binary derivation
        logger.info("Step 2: Preprocessing")
        preprocessing_main()
        logger.info("Step 2: Complete")

        # 4. Cohort Construction (T014-T016)
        # Filtering, validation, saving analysis_cohort.csv
        logger.info("Step 3: Cohort Construction & Validation")
        cohort_main()
        logger.info("Step 3: Complete")

        # 5. Bootstrap Runtime Check (T033) - Integrated into models or standalone
        # The models_main handles the runtime estimation internally before full bootstrap
        
        # 6. Modeling (T020-T024)
        # Fits OLS, bootstraps, applies FDR, saves regression_results.csv
        logger.info("Step 4: Model Fitting & Bootstrap")
        models_main()
        logger.info("Step 4: Complete")

        # 7. Save Regression Results (T024)
        # Ensures results are persisted to disk
        logger.info("Step 5: Saving Regression Results")
        save_results_main()
        logger.info("Step 5: Complete")

        # 8. Sensitivity Analysis (T027a, T027b)
        # Continuous severity and platform stratification
        logger.info("Step 6: Sensitivity Analysis")
        sensitivity_main()
        logger.info("Step 6: Complete")

        # 9. Save Sensitivity Results (T029)
        logger.info("Step 7: Saving Sensitivity Results")
        save_sensitivity_main()
        logger.info("Step 7: Complete")

        # 10. Generate Reports (T025)
        # Creates regression_summary.md
        logger.info("Step 8: Generating Reports")
        results_main()
        logger.info("Step 8: Complete")

        end_time = time.time()
        duration = end_time - start_time
        logger.info("=" * 80)
        logger.info(f"Pipeline Execution Completed Successfully in {duration:.2f} seconds")
        logger.info("=" * 80)
        return 0

    except Exception as e:
        logger.error(f"Pipeline Execution Failed: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

def main():
    """Entry point for command line execution."""
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
