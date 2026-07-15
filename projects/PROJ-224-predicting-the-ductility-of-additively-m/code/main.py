"""
Main Pipeline Orchestration for PROJ-224.

This script orchestrates the execution of the research pipeline stages.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))

from data.acquisition import main as stage_data_acquisition
from data.cleaning import main as stage_data_cleaning
from data.preprocessing import main as stage_preprocessing
from models.lme_model import main as stage_lme_modeling
from models.xgboost_model import main as stage_xgboost_modeling
from analysis.sensitivity import main as stage_sensitivity_analysis
from analysis.reporting import main as stage_reporting
from data.version_artifact import main as stage_version_artifact

logger = logging.getLogger(__name__)

# Wall clock budget in seconds (default 600, configurable via env)
WALL_CLOCK_BUDGET = int(os.getenv("WALL_CLOCK_BUDGET_SECONDS", 600))

def check_budget(start_time: float) -> bool:
    """Check if the wall clock budget has been exceeded."""
    elapsed = time.time() - start_time
    if elapsed > WALL_CLOCK_BUDGET:
        logger.error(f"Wall clock budget exceeded: {elapsed:.2f}s > {WALL_CLOCK_BUDGET}s")
        return False
    return True


def run_stage(stage_name: str, stage_func, start_time: float) -> bool:
    """
    Run a pipeline stage with budget checking.

    Args:
        stage_name: Name of the stage for logging.
        stage_func: The function to execute.
        start_time: Start time of the entire pipeline.

    Returns:
        True if the stage succeeded, False otherwise.
    """
    logger.info(f"--- Starting Stage: {stage_name} ---")
    if not check_budget(start_time):
        return False

    try:
        result = stage_func()
        if result == 0:
            logger.info(f"--- Stage Complete: {stage_name} ---")
            return True
        else:
            logger.error(f"--- Stage Failed with Error Code {result}: {stage_name} ---")
            return False
    except Exception as e:
        logger.exception(f"--- Stage Exception: {stage_name} --- Error: {e}")
        return False


def main() -> int:
    """
    Execute the full research pipeline.

    Returns:
        0 on success, non-zero on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting PROJ-224 Pipeline")
    start_time = time.time()

    stages = [
        ("Data Acquisition", stage_data_acquisition),
        ("Data Cleaning", stage_data_cleaning),
        ("Preprocessing & VIF", stage_preprocessing),
        ("LME Modeling", stage_lme_modeling),
        ("XGBoost Modeling", stage_xgboost_modeling),
        ("Sensitivity Analysis", stage_sensitivity_analysis),
        ("Artifact Versioning", stage_version_artifact),
        ("Reporting", stage_reporting),
    ]

    success = True
    for name, func in stages:
        if not check_budget(start_time):
            success = False
            break
        if not run_stage(name, func, start_time):
            success = False
            # Depending on policy, we might break here or continue
            # For now, we continue to attempt subsequent stages if possible,
            # but mark overall success as false.
            # However, if a critical dependency fails (like cleaning), later stages will fail too.
            if name in ["Data Cleaning", "Preprocessing & VIF"]:
                logger.error("Critical stage failed. Stopping pipeline.")
                break

    elapsed = time.time() - start_time
    logger.info(f"Pipeline finished in {elapsed:.2f}s")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())