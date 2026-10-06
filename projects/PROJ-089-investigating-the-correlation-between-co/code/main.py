"""
Main orchestration script for the Code Churn vs Technical Debt pipeline.
Implements T007b (Skeleton & Timeout) and T007c (Error Handling).
"""
import argparse
import logging
import signal
import sys
import time
import os
from pathlib import Path
from typing import Optional, Callable, Any

# Import public names from sibling modules as per API surface
from config import ensure_directories, get_config_summary
from utils import setup_logging, get_logger, calculate_checksum
from data_extraction import run_data_extraction_wrapper
from static_analysis import run_static_analysis
from preprocessing import run_preprocessing
from analysis import run_analysis
from visualization import run_visualization
from reporting import run_reporting

# Global timeout state
_timeout_active = False
_timeout_start_time = None
_timeout_duration = 3600 * 6  # 6 hours in seconds

# Custom TimeoutError to match API surface expectation
class TimeoutError(Exception):
    """Custom timeout exception for pipeline enforcement."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    global _timeout_active
    if _timeout_active:
        logger = get_logger("pipeline")
        logger.critical("TIMEOUT: Pipeline exceeded 6-hour limit. Aborting.")
        # Log to file specifically
        log_file = Path("data/logs/pipeline.log")
        if log_file.exists():
            with open(log_file, "a") as f:
                f.write(f"TIMEOUT: Pipeline exceeded 6-hour limit. Aborting.\n")
        raise TimeoutError("Pipeline execution exceeded 6-hour limit.")

def setup_timeout(duration_seconds: int = 3600 * 6):
    """
    Setup global watchdog for pipeline execution.
    Uses signal.SIGALRM on Linux, or a thread-based fallback on other platforms.
    """
    global _timeout_active, _timeout_duration, _timeout_start_time
    _timeout_duration = duration_seconds
    _timeout_start_time = time.time()
    _timeout_active = True

    if sys.platform == 'linux':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(duration_seconds)
    else:
        # Cross-platform fallback: Thread-based watchdog
        # Note: This is a soft check; signal-based is preferred on Linux
        import threading
        def watchdog():
            start = time.time()
            while time.time() - start < duration_seconds:
                time.sleep(60)
            if _timeout_active:
                logger = get_logger("pipeline")
                logger.critical("TIMEOUT: Pipeline exceeded 6-hour limit. Aborting.")
                log_file = Path("data/logs/pipeline.log")
                if log_file.exists():
                    with open(log_file, "a") as f:
                        f.write(f"TIMEOUT: Pipeline exceeded 6-hour limit. Aborting.\n")
                raise TimeoutError("Pipeline execution exceeded 6-hour limit.")
        
        thread = threading.Thread(target=watchdog, daemon=True)
        thread.start()

def clear_timeout():
    """Clear the active timeout state."""
    global _timeout_active
    _timeout_active = False
    if sys.platform == 'linux':
        signal.alarm(0)

def get_logger_for_pipeline(name: str = "pipeline") -> logging.Logger:
    """Get a logger instance for pipeline operations."""
    return get_logger(name)

def log_pipeline_start(logger: logging.Logger, start_time: float):
    """Log the start of the pipeline."""
    logger.info(f"Pipeline started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_file = Path("data/logs/pipeline.log")
    with open(log_file, "a") as f:
        f.write(f"START: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def log_pipeline_end(logger: logging.Logger, start_time: float):
    """Log the end of the pipeline and total duration."""
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline completed at {time.strftime('%Y-%m-%d %H:%M:%S')}. Total time: {duration:.2f}s")
    log_file = Path("data/logs/pipeline.log")
    with open(log_file, "a") as f:
        f.write(f"TOTAL_TIME: {duration:.2f}s\n")

def run_pipeline_step(step_name: str, step_func: Callable[[], Any], logger: logging.Logger) -> bool:
    """
    Execute a pipeline step with error handling (T007c).
    Wraps execution in try/except to ensure the pipeline continues on failure.
    Logs errors in the format: ERROR: {repo_id}: {message} (or generic step failure).
    """
    try:
        logger.info(f"Starting step: {step_name}")
        result = step_func()
        logger.info(f"Step {step_name} completed successfully.")
        return True
    except TimeoutError as te:
        logger.critical(f"TIMEOUT in step {step_name}: {te}")
        clear_timeout()
        raise  # Re-raise timeout to stop the pipeline immediately
    except Exception as e:
        # T007c Requirement: Log exception and continue
        error_msg = str(e)
        # If the error context contains a repo_id, use it. Otherwise use generic.
        # Since this is a general step wrapper, we log the step name and error.
        # If the step function processes specific repos internally, those should log their own repo-specific errors.
        logger.error(f"ERROR: {step_name}: {error_msg}")
        
        # Ensure logging to the specific pipeline.log file as well
        log_file = Path("data/logs/pipeline.log")
        with open(log_file, "a") as f:
            f.write(f"ERROR: {step_name}: {error_msg}\n")
        
        return False

def execute_data_extraction():
    """Wrapper for data extraction step."""
    # T010/T011/T014 logic is encapsulated here
    run_data_extraction_wrapper()

def execute_static_analysis():
    """Wrapper for static analysis step."""
    run_static_analysis()

def execute_preprocessing():
    """Wrapper for preprocessing step."""
    run_preprocessing()

def execute_analysis():
    """Wrapper for analysis step."""
    run_analysis()

def execute_visualization():
    """Wrapper for visualization step."""
    run_visualization()

def execute_reporting():
    """Wrapper for reporting step."""
    run_reporting()

def run_extraction():
    """
    T007b: Run the extraction pipeline.
    Calls the data extraction wrapper.
    """
    execute_data_extraction()

def run_analysis_task():
    """
    T007b: Run the analysis pipeline.
    Calls the analysis module.
    """
    execute_analysis()

def run_reporting_task():
    """
    T007b: Run the reporting pipeline.
    Calls the reporting module.
    """
    execute_reporting()

def run_pipeline():
    """
    T007d: Orchestration function.
    Runs the full pipeline end-to-end with error handling.
    """
    logger = get_logger("pipeline")
    start_time = time.time()
    log_pipeline_start(logger, start_time)

    # Setup timeout (T007b/T043)
    setup_timeout(_timeout_duration)

    try:
        # Step 1: Data Extraction
        if not run_pipeline_step("Data Extraction", execute_data_extraction, logger):
            logger.warning("Data Extraction failed. Continuing to next steps if possible.")
            # Depending on strictness, we might stop here. 
            # T007c says "continues execution after a repo failure", implying robustness.
            # However, if extraction fails entirely, downstream steps might crash.
            # We proceed but downstream steps will likely fail gracefully too.

        # Step 2: Static Analysis
        if not run_pipeline_step("Static Analysis", execute_static_analysis, logger):
            logger.warning("Static Analysis failed. Continuing...")

        # Step 3: Preprocessing
        if not run_pipeline_step("Preprocessing", execute_preprocessing, logger):
            logger.warning("Preprocessing failed. Continuing...")

        # Step 4: Analysis
        if not run_pipeline_step("Analysis", execute_analysis, logger):
            logger.warning("Analysis failed. Continuing...")

        # Step 5: Visualization
        if not run_pipeline_step("Visualization", execute_visualization, logger):
            logger.warning("Visualization failed. Continuing...")

        # Step 6: Reporting
        if not run_pipeline_step("Reporting", execute_reporting, logger):
            logger.warning("Reporting failed. Continuing...")

    except TimeoutError:
        # Timeout already logged in handler
        raise
    finally:
        clear_timeout()
        log_pipeline_end(logger, start_time)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Code Churn vs Technical Debt Pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--mock", action="store_true", help="Run with mock data (for testing)")
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = get_logger("pipeline")
    
    # Ensure directories exist
    ensure_directories()

    logger.info("Pipeline initialization complete.")

    if args.mock:
        logger.warning("Mock mode is not fully implemented for this pipeline. Running full pipeline with error handling.")
    
    try:
        run_pipeline()
        logger.info("Pipeline execution finished.")
    except TimeoutError:
        logger.critical("Pipeline terminated due to timeout.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline crashed with unhandled exception: {e}")
        # Log to pipeline.log specifically
        log_file = Path("data/logs/pipeline.log")
        with open(log_file, "a") as f:
            f.write(f"FATAL: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()