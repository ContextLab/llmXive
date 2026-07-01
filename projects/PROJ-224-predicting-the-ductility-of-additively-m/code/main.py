"""
Main entry point for the full pipeline integration test (T038).
Orchestrates the end-to-end execution of data acquisition, cleaning,
preprocessing, modeling (LME and XGBoost), and reporting.
Ensures execution completes within the 600s time budget.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Time budget
TIME_BUDGET_SECONDS = 600
START_TIME = time.time()

def check_budget():
    elapsed = time.time() - START_TIME
    if elapsed > TIME_BUDGET_SECONDS:
        raise TimeoutError(f"Pipeline execution exceeded time budget of {TIME_BUDGET_SECONDS}s. Elapsed: {elapsed:.2f}s")
    logger.info(f"Time check passed. Elapsed: {elapsed:.2f}s / {TIME_BUDGET_SECONDS}s")

def run_stage(name, func, *args, **kwargs):
    logger.info(f"--- Starting Stage: {name} ---")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"--- Stage {name} completed in {elapsed:.2f}s ---")
        check_budget()
        return result
    except Exception as e:
        logger.error(f"--- Stage {name} FAILED: {str(e)} ---")
        raise

def stage_data_acquisition():
    from data.acquisition import main as acquisition_main
    return acquisition_main()

def stage_data_cleaning():
    from data.cleaning import main as cleaning_main
    return cleaning_main()

def stage_preprocessing():
    from data.preprocessing import main as preprocessing_main
    return preprocessing_main()

def stage_lme_modeling():
    from models.lme_model import main as lme_main
    from models.save_lme_artifact import main as save_lme_main
    lme_main()
    save_lme_main()

def stage_xgboost_modeling():
    from models.xgboost_model import main as xgb_main
    from models.save_predictive_artifact import main as save_xgb_main
    xgb_main()
    save_xgb_main()

def stage_sensitivity_analysis():
    from analysis.sensitivity import main as sensitivity_main
    return sensitivity_main()

def stage_reporting():
    from analysis.reporting import main as reporting_main
    return reporting_main()

def main():
    logger.info("Starting Full Pipeline Integration Test (T038)")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Time Budget: {TIME_BUDGET_SECONDS}s")

    try:
        # 1. Data Acquisition
        run_stage("Data Acquisition", stage_data_acquisition)

        # 2. Data Cleaning
        run_stage("Data Cleaning", stage_data_cleaning)

        # 3. Preprocessing (Energy Density, VIF, Split)
        run_stage("Preprocessing", stage_preprocessing)

        # 4. LME Modeling
        run_stage("LME Modeling", stage_lme_modeling)

        # 5. XGBoost Modeling
        run_stage("XGBoost Modeling", stage_xgboost_modeling)

        # 6. Sensitivity Analysis
        run_stage("Sensitivity Analysis", stage_sensitivity_analysis)

        # 7. Final Reporting
        run_stage("Final Reporting", stage_reporting)

        total_elapsed = time.time() - START_TIME
        logger.info("=" * 50)
        logger.info(f"PIPELINE INTEGRATION TEST PASSED")
        logger.info(f"Total Execution Time: {total_elapsed:.2f}s")
        logger.info(f"Status: SUCCESS (Within {TIME_BUDGET_SECONDS}s budget)")
        logger.info("=" * 50)
        return 0

    except TimeoutError as e:
        logger.error(f"PIPELINE FAILED: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"PIPELINE FAILED with unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())