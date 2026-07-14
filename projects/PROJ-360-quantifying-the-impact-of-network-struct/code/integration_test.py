"""
Integration test for the full pipeline: download -> construct -> metrics -> analyze -> report.
Verifies end-to-end data flow and measures total runtime against the 6-hour limit.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Import pipeline stages
from download import main as download_main
from construct_network import main as construct_main
from compute_metrics import main as compute_metrics_main
from analyze import main as analyze_main
from report import main as report_main
from runtime_monitor import record_start_time, measure_and_log_runtime, setup_runtime_logger
from utils import setup_logging, pin_seed

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_FILE = RESULTS_DIR / "integration_test.log"
RUNTIME_LOG = RESULTS_DIR / "runtime.log"
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours

def setup_integration_logger():
    """Setup logger for integration test."""
    setup_logging(LOG_FILE, level=logging.INFO)
    logger = logging.getLogger("integration_test")
    logger.info("Integration test started.")
    return logger

def check_artifacts_exist():
    """Verify all expected artifacts exist after pipeline run."""
    required_files = [
        PROJECT_ROOT / "data" / "raw" / "cif",
        PROJECT_ROOT / "data" / "processed" / "networks",
        PROJECT_ROOT / "data" / "processed" / "network_manifest.json",
        PROJECT_ROOT / "data" / "processed" / "metrics.csv",
        PROJECT_ROOT / "results" / "correlations.json",
        PROJECT_ROOT / "data" / "processed" / "filtered_features.csv",
        PROJECT_ROOT / "models" / "thermal_predictor.pkl",
        PROJECT_ROOT / "results" / "model_performance.json",
        PROJECT_ROOT / "results" / "final_report.md",
        PROJECT_ROOT / "results" / "runtime.log",
    ]
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f))
    
    if missing:
        raise FileNotFoundError(f"Missing required artifacts: {missing}")
    return True

def run_pipeline():
    """Execute the full pipeline stages sequentially."""
    logger = setup_integration_logger()
    
    # Pin seed for reproducibility
    pin_seed(42)
    logger.info("Seed pinned for reproducibility.")

    # Record start time for runtime monitoring
    record_start_time(RUNTIME_LOG)
    logger.info("Pipeline start time recorded.")

    try:
        # Stage 1: Download
        logger.info("Starting Stage 1: Download CIF files...")
        # We assume the download script is designed to be idempotent or skip existing
        # If it requires args, we'd pass them here, but main() usually handles defaults
        download_main()
        logger.info("Stage 1 complete: CIF files downloaded.")

        # Stage 2: Construct Networks
        logger.info("Starting Stage 2: Construct atomic networks...")
        construct_main()
        logger.info("Stage 2 complete: Networks constructed.")

        # Stage 3: Compute Metrics
        logger.info("Starting Stage 3: Compute network metrics...")
        compute_metrics_main()
        logger.info("Stage 3 complete: Metrics computed.")

        # Stage 4: Analyze (VIF, Model, CV)
        logger.info("Starting Stage 4: Analyze data and train model...")
        analyze_main()
        logger.info("Stage 4 complete: Analysis and model training done.")

        # Stage 5: Report
        logger.info("Starting Stage 5: Generate final report...")
        report_main()
        logger.info("Stage 5 complete: Report generated.")

        # Measure runtime
        runtime_seconds = measure_and_log_runtime(RUNTIME_LOG)
        logger.info(f"Total pipeline runtime: {runtime_seconds:.2f} seconds")

        if runtime_seconds > MAX_RUNTIME_SECONDS:
            logger.error(f"Runtime exceeded limit: {runtime_seconds:.2f}s > {MAX_RUNTIME_SECONDS}s")
            return False, f"Runtime exceeded 6 hours: {runtime_seconds:.2f}s"

        # Verify artifacts
        logger.info("Verifying artifacts...")
        check_artifacts_exist()
        logger.info("All artifacts verified.")

        logger.info("Integration test PASSED.")
        return True, "Pipeline completed successfully within time limit."

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        return False, str(e)

def main():
    """Entry point for integration test."""
    success, message = run_pipeline()
    print(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
