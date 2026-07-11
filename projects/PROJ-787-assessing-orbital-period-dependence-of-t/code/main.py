"""
Main entry point for the Exoplanet Radius Gap Analysis Pipeline.

Orchestrates the full pipeline execution with runtime monitoring.
Enforces a hard limit of 6 hours (21600 seconds) on total execution time.
"""
import os
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import timedelta

# Configure logging early
from utils.logging_config import setup_logging, get_logger
from utils.setup_dirs import initialize_directories

# Import pipeline stages
from ingest.download_dr25 import main as download_dr25_main
from ingest.download_kic import main as download_kic_main
from ingest.download_completeness import main as download_completeness_main
from ingest.merge_catalogs import main as merge_catalogs_main
from ingest.preprocess import main as preprocess_main
from analysis.binning import main as binning_main
from analysis.gmm_fitter import main as gmm_main
from analysis.binned_stats import main as binned_stats_main
from analysis.regression import main as regression_main
from theory.scaling_laws import main as scaling_laws_main
from theory.theory_comparison import main as theory_comparison_main
from validation.synthetic_recovery import main as synthetic_recovery_main

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours in seconds
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

def run_pipeline_step(step_name: str, step_func: callable, logger: logging.Logger) -> bool:
    """
    Execute a pipeline step with timing and error handling.
    
    Args:
        step_name: Human-readable name of the step
        step_func: Function to execute (should be a main() style function)
        logger: Logger instance for this step
        
    Returns:
        True if step succeeded, False otherwise
    """
    logger.info(f"Starting step: {step_name}")
    try:
        # Execute the step
        step_func()
        logger.info(f"Completed step: {step_name}")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Step {step_name} failed with exit code {e.code}")
            return False
        logger.info(f"Step {step_name} completed with exit code 0")
        return True
    except Exception as e:
        logger.error(f"Step {step_name} failed with exception: {e}", exc_info=True)
        return False

def check_runtime(start_time: float, logger: logging.Logger) -> None:
    """
    Check if runtime has exceeded the 6-hour limit.
    
    Args:
        start_time: Pipeline start time (from time.time())
        logger: Logger instance
        
    Raises:
        SystemExit: If runtime exceeds 6 hours
    """
    elapsed = time.time() - start_time
    elapsed_str = str(timedelta(seconds=int(elapsed)))
    
    if elapsed > MAX_RUNTIME_SECONDS:
        logger.error("Runtime exceeded 6h")
        logger.error(f"Total elapsed time: {elapsed_str}")
        raise SystemExit(1)
    
    # Log progress every 30 minutes
    if int(elapsed) % (30 * 60) < 10:  # Log near the 30-minute mark
        logger.info(f"Pipeline progress: {elapsed_str} elapsed")

def main():
    """
    Main entry point for the pipeline.
    
    Executes all pipeline stages in order with runtime monitoring.
    Fails the build if total runtime exceeds 6 hours.
    """
    start_time = time.time()
    
    # Setup logging
    log_file = LOG_DIR / f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_logging(log_file=log_file, level=logging.INFO)
    logger.info("Exoplanet Radius Gap Analysis Pipeline started")
    logger.info(f"Maximum allowed runtime: {timedelta(seconds=MAX_RUNTIME_SECONDS)}")
    
    # Initialize directories
    initialize_directories()
    
    # Define pipeline stages in execution order
    pipeline_stages = [
        ("Download DR25 Planet Table", download_dr25_main),
        ("Download KIC Catalog", download_kic_main),
        ("Download Completeness Map", download_completeness_main),
        ("Merge Catalogs", merge_catalogs_main),
        ("Preprocess and Filter Data", preprocess_main),
        ("Bin Planets by Period", binning_main),
        ("Fit GMM to Radius Distribution", gmm_main),
        ("Calculate Binned Statistics", binned_stats_main),
        ("Perform Regression Analysis", regression_main),
        ("Load and Process Theoretical Laws", scaling_laws_main),
        ("Compare with Theoretical Models", theory_comparison_main),
        ("Run Synthetic Recovery Validation", synthetic_recovery_main),
    ]
    
    # Execute pipeline stages
    success = True
    for step_name, step_func in pipeline_stages:
        # Check runtime before each step
        check_runtime(start_time, logger)
        
        if not run_pipeline_step(step_name, step_func, logger):
            success = False
            logger.error(f"Pipeline failed at step: {step_name}")
            break
        
        # Check runtime after each step
        check_runtime(start_time, logger)
    
    # Final runtime check
    check_runtime(start_time, logger)
    
    elapsed_time = time.time() - start_time
    elapsed_str = str(timedelta(seconds=int(elapsed_time)))
    
    if success:
        logger.info(f"Pipeline completed successfully in {elapsed_str}")
        sys.exit(0)
    else:
        logger.error(f"Pipeline failed after {elapsed_str}")
        sys.exit(1)

if __name__ == "__main__":
    main()