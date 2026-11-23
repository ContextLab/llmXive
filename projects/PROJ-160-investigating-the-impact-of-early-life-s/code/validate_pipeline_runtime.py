"""
T045: Verify total pipeline runtime (Acquisition -> Robustness) is <= 6 hours (SC-006).

This script orchestrates the full pipeline execution (Acquisition -> Preprocessing -> Modeling -> Robustness)
and measures the total wall-clock time. It asserts that the total time does not exceed 6 hours (21,600 seconds).

It uses the existing modules defined in the project API surface to perform the actual work,
ensuring that the verification is based on real execution, not simulation.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path to allow relative imports if run as script
# (Though typically run via `python -m code.validate_pipeline_runtime`)
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_project_root, get_processed_dir, ensure_directories
from code.main import setup_logging, run_pipeline, PipelineError
from code.analysis.robustness import main as robustness_main
from code.data.acquisition import main as acquisition_main
from code.data.preprocessing import main as preprocessing_main
from code.analysis.modeling import main as modeling_main
from code.analysis.save_results import main as save_results_main
from code.analysis.aggregate_robustness import main as aggregate_main

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
LOG_FILE = "logs/pipeline_runtime_verification.log"

def log_step(message: str, logger: logging.Logger):
    """Log a step message with timestamp."""
    logger.info(f"[{time.strftime('%H:%M:%S')}] {message}")
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_full_pipeline(logger: logging.Logger) -> float:
    """
    Execute the full pipeline stages sequentially and return total elapsed time.
    Stages:
    1. Acquisition (Download/Verify)
    2. Preprocessing (Filter/Normalize/Transform)
    3. Modeling (LMM fitting)
    4. Robustness (Permutations/Sensitivity)
    5. Save Results & Aggregate
    """
    start_time = time.time()
    ensure_directories()

    # Stage 1: Acquisition
    log_step("Starting Data Acquisition...", logger)
    try:
        # We call the main function of acquisition. 
        # Note: In a real CI/CD, this might download huge files. 
        # The task requires verifying runtime <= 6h. 
        # If data is already present, this step should be fast.
        # We wrap in try/except to fail loudly if data source is unreachable.
        acquisition_main()
    except Exception as e:
        logger.error(f"Acquisition failed: {e}")
        raise PipelineError(f"Acquisition stage failed: {e}")
    
    # Stage 2: Preprocessing
    log_step("Starting Data Preprocessing...", logger)
    try:
        preprocessing_main()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise PipelineError(f"Preprocessing stage failed: {e}")

    # Stage 3: Modeling
    log_step("Starting Statistical Modeling...", logger)
    try:
        modeling_main()
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        raise PipelineError(f"Modeling stage failed: {e}")

    # Stage 4: Robustness (Permutation tests - most time consuming)
    log_step("Starting Robustness Validation (Permutations)...", logger)
    try:
        robustness_main()
    except Exception as e:
        logger.error(f"Robustness failed: {e}")
        raise PipelineError(f"Robustness stage failed: {e}")

    # Stage 5: Save Results
    log_step("Saving Results...", logger)
    try:
        save_results_main()
    except Exception as e:
        logger.error(f"Save Results failed: {e}")
        raise PipelineError(f"Save Results stage failed: {e}")

    # Stage 6: Aggregate Robustness
    log_step("Aggregating Robustness Metrics...", logger)
    try:
        aggregate_main()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise PipelineError(f"Aggregation stage failed: {e}")

    end_time = time.time()
    return end_time - start_time

def main():
    """Main entry point for T045 verification."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / LOG_FILE

    # Setup logging
    logger = setup_logging(log_file=str(log_path))
    
    log_step("========================================", logger)
    log_step("Pipeline Runtime Verification (T045)", logger)
    log_step(f"Max Allowed Runtime: {MAX_RUNTIME_SECONDS / 3600:.1f} hours", logger)
    log_step("========================================", logger)

    total_runtime = 0.0
    try:
        total_runtime = run_full_pipeline(logger)
    except PipelineError as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"\nVERIFICATION FAILED: Pipeline execution error - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline: {e}")
        print(f"\nVERIFICATION FAILED: Unexpected error - {e}")
        sys.exit(1)

    hours = total_runtime / 3600
    minutes = (total_runtime % 3600) / 60
    seconds = total_runtime % 60

    log_step("========================================", logger)
    log_step(f"TOTAL RUNTIME: {hours:.2f} hours ({minutes:.1f} min, {seconds:.1f} sec)", logger)
    log_step("========================================", logger)

    if total_runtime <= MAX_RUNTIME_SECONDS:
        log_step("SUCCESS: Pipeline completed within the 6-hour limit.", logger)
        print(f"\nVERIFICATION PASSED: Runtime ({hours:.2f}h) <= 6h")
        sys.exit(0)
    else:
        log_step("FAILURE: Pipeline exceeded the 6-hour limit.", logger)
        print(f"\nVERIFICATION FAILED: Runtime ({hours:.2f}h) > 6h")
        sys.exit(1)

if __name__ == "__main__":
    main()