"""
Main entry point for the full pipeline.
Orchestrates data acquisition, cleaning, preprocessing, modeling, and reporting.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.acquisition import main as stage_data_acquisition
from data.cleaning import main as stage_data_cleaning
from data.preprocessing import main as stage_preprocessing
from models.lme_model import main as stage_lme_modeling
from models.xgboost_model import main as stage_xgboost_modeling
from analysis.sensitivity import main as stage_sensitivity_analysis
from analysis.reporting import main as stage_reporting

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BUDGET_SECONDS = 600

def check_budget(start_time):
    """Check if execution time exceeds budget."""
    elapsed = time.time() - start_time
    if elapsed > BUDGET_SECONDS:
        logger.error(f"Execution exceeded budget of {BUDGET_SECONDS}s at {elapsed:.1f}s")
        return False
    return True

def run_stage(stage_name, stage_func):
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"Starting stage: {stage_name}")
    start = time.time()
    try:
        stage_func()
        elapsed = time.time() - start
        logger.info(f"Stage {stage_name} completed in {elapsed:.2f}s")
        if not check_budget(start):
            return False
        return True
    except Exception as e:
        logger.error(f"Stage {stage_name} failed with error: {e}", exc_info=True)
        return False

def stage_data_acquisition():
    """Wrapper for data acquisition stage."""
    stage_data_acquisition()

def stage_data_cleaning():
    """Wrapper for data cleaning stage."""
    stage_data_cleaning()

def stage_preprocessing():
    """Wrapper for data preprocessing stage."""
    stage_preprocessing()

def stage_lme_modeling():
    """Wrapper for LME modeling stage."""
    stage_lme_modeling()

def stage_xgboost_modeling():
    """Wrapper for XGBoost modeling stage."""
    stage_xgboost_modeling()

def stage_sensitivity_analysis():
    """Wrapper for sensitivity analysis stage."""
    stage_sensitivity_analysis()

def stage_reporting():
    """Wrapper for reporting stage."""
    stage_reporting()

def main():
    """Execute the full pipeline."""
    logger.info("Starting full pipeline execution...")
    start_time = time.time()

    stages = [
        ("Data Acquisition", stage_data_acquisition),
        ("Data Cleaning", stage_data_cleaning),
        ("Preprocessing", stage_preprocessing),
        ("LME Modeling", stage_lme_modeling),
        ("XGBoost Modeling", stage_xgboost_modeling),
        ("Sensitivity Analysis", stage_sensitivity_analysis),
        ("Reporting", stage_reporting),
    ]

    success = True
    for name, func in stages:
        if not check_budget(start_time):
            success = False
            break
        if not run_stage(name, func):
            success = False
            break

    total_time = time.time() - start_time
    
    if success:
        logger.info(f"Pipeline completed successfully in {total_time:.2f}s (Budget: {BUDGET_SECONDS}s)")
        return 0
    else:
        logger.error(f"Pipeline failed or timed out after {total_time:.2f}s")
        return 1

if __name__ == "__main__":
    sys.exit(main())