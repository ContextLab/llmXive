import argparse
import logging
import signal
import sys
import time
import os
import traceback
from pathlib import Path
from typing import Callable, Any, Optional, Dict
import pandas as pd

from config import ensure_directories, get_config_summary
from utils import setup_logging, get_logger
from data_extraction import run_data_extraction_wrapper
from static_analysis import run_static_analysis
from preprocessing import run_preprocessing
from analysis import run_analysis
from visualization import run_visualization
from reporting import run_reporting

# Global timeout state
_timeout_timer = None
_start_time = None
_pipeline_timeout = 6 * 3600  # 6 hours in seconds

class TimeoutError(Exception):
    """Custom timeout error for pipeline execution."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Pipeline execution exceeded {_pipeline_timeout} seconds")

def setup_timeout(timeout_seconds: Optional[int] = None):
    """Setup global timeout for the pipeline."""
    global _pipeline_timeout, _timeout_timer, _start_time
    if timeout_seconds:
        _pipeline_timeout = timeout_seconds
    
    _start_time = time.time()
    
    # Use signal for Linux, Timer for others
    if sys.platform == 'linux':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(_pipeline_timeout)
    else:
        def check_timeout():
            if time.time() - _start_time > _pipeline_timeout:
                raise TimeoutError(f"Pipeline execution exceeded {_pipeline_timeout} seconds")
        import threading
        _timeout_timer = threading.Timer(_pipeline_timeout, check_timeout)
        _timeout_timer.daemon = True
        _timeout_timer.start()

def clear_timeout():
    """Clear the timeout timer."""
    global _timeout_timer
    if sys.platform == 'linux':
        signal.alarm(0)
    elif _timeout_timer:
        _timeout_timer.cancel()
        _timeout_timer = None

def get_logger_for_pipeline():
    """Get the logger for pipeline logging."""
    return get_logger("pipeline")

def log_pipeline_start():
    """Log pipeline start time."""
    logger = get_logger_for_pipeline()
    logger.info("Pipeline started")

def log_pipeline_end():
    """Log pipeline end time and duration."""
    logger = get_logger_for_pipeline()
    if _start_time:
        duration = time.time() - _start_time
        logger.info(f"TOTAL_TIME: {duration:.2f}s")
    else:
        logger.info("TOTAL_TIME: unknown (start time not recorded)")

def run_pipeline_step(step_name: str, func: Callable, *args, **kwargs) -> Any:
    """
    Generic wrapper to run a pipeline step with logging and error handling.
    This is for high-level steps, not per-repo processing.
    """
    logger = get_logger_for_pipeline()
    logger.info(f"Starting step: {step_name}")
    try:
        result = func(*args, **kwargs)
        logger.info(f"Completed step: {step_name}")
        return result
    except Exception as e:
        logger.error(f"ERROR: {step_name}: {str(e)}")
        # Re-raise to stop pipeline on critical step failure
        raise

def execute_data_extraction():
    """Execute data extraction step."""
    return run_data_extraction_wrapper()

def execute_static_analysis():
    """Execute static analysis step."""
    return run_static_analysis()

def execute_preprocessing():
    """Execute preprocessing step."""
    return run_preprocessing()

def execute_analysis():
    """Execute analysis step."""
    return run_analysis()

def execute_visualization():
    """Execute visualization step."""
    return run_visualization()

def execute_reporting():
    """Execute reporting step."""
    return run_reporting()

def run_extraction() -> pd.DataFrame:
    """
    Run the data extraction pipeline.
    Returns the unified metrics DataFrame.
    """
    logger = get_logger_for_pipeline()
    logger.info("Running data extraction...")
    
    # This function delegates to the wrapper which handles per-repo logic
    # The wrapper in data_extraction.py handles the per-repo try/except
    try:
        result = execute_data_extraction()
        logger.info("Data extraction completed successfully")
        return result
    except Exception as e:
        logger.error(f"ERROR: Data extraction failed: {str(e)}")
        raise

def run_analysis_task() -> dict:
    """
    Run the analysis pipeline.
    Returns the analysis results dictionary.
    """
    logger = get_logger_for_pipeline()
    logger.info("Running analysis...")
    
    try:
        result = execute_analysis()
        logger.info("Analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"ERROR: Analysis failed: {str(e)}")
        raise

def run_reporting_task() -> None:
    """
    Run the reporting pipeline.
    """
    logger = get_logger_for_pipeline()
    logger.info("Running reporting...")
    
    try:
        execute_reporting()
        logger.info("Reporting completed successfully")
    except Exception as e:
        logger.error(f"ERROR: Reporting failed: {str(e)}")
        raise

def run_pipeline(timeout_seconds: Optional[int] = None):
    """
    Run the full pipeline end-to-end.
    Implements orchestration with error handling for each major step.
    """
    logger = get_logger_for_pipeline()
    
    # Setup timeout
    setup_timeout(timeout_seconds)
    
    try:
        log_pipeline_start()
        
        # Step 1: Data Extraction
        run_pipeline_step("extraction", run_extraction)
        
        # Step 2: Static Analysis (if needed, though often integrated in extraction)
        # Note: Based on task flow, static analysis might be part of extraction or separate
        # We'll call it if the pipeline design expects it here
        # run_pipeline_step("static_analysis", execute_static_analysis)
        
        # Step 3: Preprocessing
        run_pipeline_step("preprocessing", execute_preprocessing)
        
        # Step 4: Analysis
        run_pipeline_step("analysis", run_analysis_task)
        
        # Step 5: Visualization
        run_pipeline_step("visualization", execute_visualization)
        
        # Step 6: Reporting
        run_pipeline_step("reporting", run_reporting_task)
        
        log_pipeline_end()
        logger.info("Pipeline completed successfully")
        
    except TimeoutError as e:
        logger.error(f"ERROR: Pipeline timeout: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"ERROR: Pipeline failed: {str(e)}")
        raise
    finally:
        clear_timeout()

def main():
    """Main entry point for the pipeline."""
    # Setup logging
    ensure_directories()
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Code Churn and Technical Debt Analysis Pipeline")
    parser.add_argument("--timeout", type=int, default=6*3600, help="Pipeline timeout in seconds")
    parser.add_argument("--step", type=str, choices=["extraction", "analysis", "reporting", "full"], 
                      default="full", help="Pipeline step to run")
    
    args = parser.parse_args()
    
    try:
        if args.step == "full":
            run_pipeline(timeout_seconds=args.timeout)
        elif args.step == "extraction":
            run_pipeline_step("extraction", run_extraction)
        elif args.step == "analysis":
            run_pipeline_step("analysis", run_analysis_task)
        elif args.step == "reporting":
            run_pipeline_step("reporting", run_reporting_task)
    except Exception as e:
        print(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
