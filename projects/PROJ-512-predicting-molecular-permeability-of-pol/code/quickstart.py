"""
Quickstart script to validate the entire pipeline execution.
Runs ingestion, preprocessing, model training, evaluation, and statistical analysis.
Verifies production of required artifacts: polymers.h5, metrics.json, sensitivity_sweep.json.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.utils import setup_logging, set_seed
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from models.trainer import main as training_main
from evaluation.metrics import main as metrics_main
from evaluation.stats import main as stats_main
from evaluation.report import main as report_main

# Configure logging
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "quickstart_run.log"
setup_logging(level=logging.INFO, log_file=str(log_file))
logger = logging.getLogger(__name__)

# Constants for artifact verification
REQUIRED_ARTIFACTS = {
    "polymers.h5": PROJECT_ROOT / "data" / "processed" / "polymers.h5",
    "metrics.json": PROJECT_ROOT / "evaluation" / "results" / "metrics.json",
    "sensitivity_sweep.json": PROJECT_ROOT / "evaluation" / "results" / "sensitivity_sweep.json"
}

def run_step(step_name, step_func):
    """Execute a pipeline step with timing and error handling."""
    logger.info(f"--- Starting {step_name} ---")
    start_time = time.time()
    try:
        step_func()
        duration = time.time() - start_time
        logger.info(f"--- {step_name} completed successfully in {duration:.2f}s ---")
        return True
    except Exception as e:
        logger.error(f"--- {step_name} FAILED: {str(e)} ---")
        raise

def verify_artifacts():
    """Check that all required output files exist and are non-empty."""
    logger.info("--- Verifying Artifacts ---")
    all_present = True
    for name, path in REQUIRED_ARTIFACTS.items():
        if path.exists() and path.stat().st_size > 0:
            logger.info(f"  [OK] {name} exists ({path.stat().st_size} bytes)")
        else:
            logger.error(f"  [MISSING] {name} at {path}")
            all_present = False

    if not all_present:
        missing = [name for name, path in REQUIRED_ARTIFACTS.items() if not path.exists()]
        raise FileNotFoundError(f"Missing required artifacts: {missing}")
    
    logger.info("--- All required artifacts verified ---")
    return True

def main():
    """Execute the full quickstart validation pipeline."""
    logger.info("Starting Quickstart Validation Pipeline (T064)")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    # Set seed for reproducibility
    set_seed(42)

    try:
        # 1. Data Ingestion (T010, T011a, T011b, T012)
        run_step("Data Ingestion", ingestion_main)

        # 2. Preprocessing & Splitting (T013, T014, T020)
        run_step("Preprocessing", preprocessing_main)

        # 3. Model Training (T021, T022, T023, T024a, T024b, T024c, T029)
        run_step("Model Training", training_main)

        # 4. Metrics Calculation (T025)
        run_step("Metrics Calculation", metrics_main)

        # 5. Statistical Analysis (T031, T032, T033, T034)
        run_step("Statistical Analysis", stats_main)

        # 6. Report Generation (T035, T026)
        run_step("Report Generation", report_main)

        # 7. Verify Output Artifacts
        verify_artifacts()

        logger.info("========================================")
        logger.info("QUICKSTART VALIDATION: SUCCESS")
        logger.info("All pipeline steps executed without error.")
        logger.info("Required artifacts produced:")
        for name in REQUIRED_ARTIFACTS.keys():
            logger.info(f"  - {name}")
        logger.info("========================================")
        return 0

    except Exception as e:
        logger.error("========================================")
        logger.error("QUICKSTART VALIDATION: FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error("========================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())
