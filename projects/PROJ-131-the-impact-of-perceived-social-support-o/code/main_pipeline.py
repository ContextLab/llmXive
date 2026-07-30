"""
Main Pipeline Orchestrator for the Social Support Resilience Project.

This script chains all phases of the research pipeline:
1. Ingestion (T012)
2. Preprocessing (T013)
3. Cohort Construction & Validation (T014-T016)
4. Modeling & Bootstrapping (T020-T024)
5. Sensitivity Analysis (T027-T030)
6. Reporting (T025)

Dependencies:
- All Phase 1-5 tasks must be complete before running this orchestrator.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Add project root to path to ensure imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logger import get_logger

from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main
from analysis.validation import main as validation_main
from analysis.models import main as models_main
from analysis.sensitivity_compare import main as sensitivity_compare_main
from analysis.results import main as results_main
from analysis.save_regression_results import main as save_results_main
from analysis.save_sensitivity_results import main as save_sensitivity_main
from analysis.bootstrap_ci import main as bootstrap_main
from analysis.fdr_correction import main as fdr_main

logger = get_logger(__name__)

def run_pipeline():
    """
    Executes the full research pipeline in the correct order.
    
    Order:
    1. Ingestion
    2. Preprocessing
    3. Cohort Construction
    4. Validation
    5. Modeling (OLS + Bootstrap + FDR)
    6. Sensitivity Analysis
    7. Reporting
    """
    start_time = time.time()
    logger.info("Starting Main Pipeline Execution")
    
    # Phase 1: Ingestion (T012)
    logger.info("Phase 1: Data Ingestion")
    try:
        ingestion_main()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

    # Phase 2: Preprocessing (T013)
    logger.info("Phase 2: Preprocessing & Imputation")
    try:
        preprocessing_main()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # Phase 3: Cohort Construction (T014)
    logger.info("Phase 3: Cohort Construction")
    try:
        cohort_main()
    except Exception as e:
        logger.error(f"Cohort construction failed: {e}")
        raise

    # Phase 3b: Validation (T015)
    logger.info("Phase 3b: Cohort Validation")
    try:
        validation_main()
    except Exception as e:
        logger.error(f"Cohort validation failed: {e}")
        raise

    # Phase 4: Modeling (T020)
    logger.info("Phase 4: Model Fitting (OLS)")
    try:
        models_main()
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

    # Phase 4b: Bootstrapping (T021)
    logger.info("Phase 4b: Bootstrapping CIs")
    try:
        bootstrap_main()
    except Exception as e:
        logger.error(f"Bootstrapping failed: {e}")
        raise

    # Phase 4c: FDR Correction (T023)
    logger.info("Phase 4c: FDR Correction")
    try:
        fdr_main()
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        raise

    # Phase 4d: Save Regression Results (T024)
    logger.info("Phase 4d: Saving Regression Results")
    try:
        save_results_main()
    except Exception as e:
        logger.error(f"Saving regression results failed: {e}")
        raise

    # Phase 5: Sensitivity Analysis (T027)
    logger.info("Phase 5: Sensitivity Analysis")
    try:
        sensitivity_compare_main()
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

    # Phase 5b: Save Sensitivity Results (T029)
    logger.info("Phase 5b: Saving Sensitivity Results")
    try:
        save_sensitivity_main()
    except Exception as e:
        logger.error(f"Saving sensitivity results failed: {e}")
        raise

    # Phase 6: Reporting (T025)
    logger.info("Phase 6: Generating Reports")
    try:
        results_main()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
    return True

def main():
    """Entry point for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / "data" / "logs" / "pipeline.log")
        ]
    )
    
    # Ensure log directory exists
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        run_pipeline()
    except Exception as e:
        logger.exception("Pipeline execution failed with fatal error")
        sys.exit(1)

if __name__ == "__main__":
    main()