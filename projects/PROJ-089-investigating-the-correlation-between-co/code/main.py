import argparse
import logging
import signal
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any

# Import existing pipeline stages from sibling modules
# These functions are defined in the API surface provided
from data_extraction import run_data_extraction_wrapper as run_extraction
from analysis import run_analysis
from visualization import run_visualization
from reporting import run_reporting
from config import ensure_directories, get_config_summary
from utils import setup_logging, get_logger, pin_random_seed

# Constants
PIPELINE_TIMEOUT_SECONDS = 6 * 60 * 60  # 6 hours
PIPELINE_LOG_PATH = "data/logs/pipeline.log"

# Global flag for timeout
_timeout_active = False

class TimeoutError(Exception):
    """Custom timeout exception for pipeline execution."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Pipeline execution exceeded {PIPELINE_TIMEOUT_SECONDS} seconds (6 hours).")

def setup_timeout():
    """Configure the 6-hour timeout using signal."""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(PIPELINE_TIMEOUT_SECONDS)
    else:
        # Fallback for Windows or environments without SIGALRM
        logging.warning("SIGALRM not available. Timeout enforcement disabled.")

def clear_timeout():
    """Cancel the alarm if the pipeline finishes successfully."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

def run_pipeline_step(step_name: str, step_func: Callable, *args, **kwargs) -> bool:
    """
    Execute a pipeline step with error handling and logging.
    Returns True if successful, False if an exception occurred.
    """
    logger = get_logger()
    start_time = time.time()
    try:
        logger.info(f"Starting step: {step_name}")
        step_func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Completed step: {step_name} in {duration:.2f}s")
        return True
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Step {step_name} failed after {duration:.2f}s with error: {str(e)}", exc_info=True)
        # Per T007c: Continue to next step even if one fails
        return False

def execute_data_extraction(config: Dict[str, Any]):
    """Wrapper for data extraction stage."""
    run_extraction(config)

def execute_static_analysis(config: Dict[str, Any]):
    """Wrapper for static analysis stage (usually handled within extraction or preprocessing, but kept for orchestration)."""
    # In this architecture, static analysis is often part of the extraction/preprocessing flow.
    # If a separate call is needed, it would be here. For now, we rely on run_extraction to handle
    # the full data gathering including static analysis as per T014.
    pass

def execute_preprocessing(config: Dict[str, Any]):
    """Wrapper for preprocessing stage."""
    from preprocessing import run_preprocessing
    run_preprocessing(config)

def execute_analysis(config: Dict[str, Any]):
    """Wrapper for analysis stage."""
    run_analysis(config)

def execute_visualization(config: Dict[str, Any]):
    """Wrapper for visualization stage."""
    run_visualization(config)

def execute_reporting(config: Dict[str, Any]):
    """Wrapper for reporting stage."""
    run_reporting(config)

def run_extraction_wrapper(config: Dict[str, Any]):
    """
    Orchestrates the extraction phase.
    Calls run_data_extraction_wrapper which handles repo selection, cloning, git metrics, and static analysis.
    """
    # Ensure the extraction module's main logic is triggered
    # The API surface shows run_data_extraction_wrapper exists.
    run_extraction(config)

def run_analysis_phase(config: Dict[str, Any]):
    """
    Orchestrates the analysis phase.
    """
    run_analysis(config)

def run_reporting_phase(config: Dict[str, Any]):
    """
    Orchestrates the reporting phase.
    """
    run_reporting(config)

def run_pipeline(config: Optional[Dict[str, Any]] = None):
    """
    Main orchestration function.
    Runs the full pipeline end-to-end:
    1. run_extraction (Data Acquisition & Preprocessing)
    2. run_analysis (Statistical Correlation)
    3. run_reporting (Visualization & Reporting)

    Implements timeout and error handling as per T007b and T007c.
    """
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_file=str(Path(log_dir) / "pipeline.log"))
    
    if not config:
        config = get_config_summary()
    
    logger.info("Pipeline started.")
    logger.info(f"Configuration: {config}")
    
    # Pin random seed for reproducibility
    pin_random_seed(config.get('random_seed', 42))

    # Setup timeout
    setup_timeout()

    total_start = time.time()
    success = True

    try:
        # Step 1: Extraction (Includes T010-T014 logic via run_data_extraction_wrapper)
        # This stage produces data/processed/unified_metrics.csv
        if not run_pipeline_step("Data Extraction", run_extraction_wrapper, config):
            success = False
            logger.warning("Data extraction failed. Proceeding to analysis with available data (if any).")

        # Step 2: Analysis (T018-T023)
        # Requires data/processed/unified_metrics.csv
        if not run_pipeline_step("Statistical Analysis", run_analysis_phase, config):
            success = False
            logger.warning("Analysis failed. Proceeding to reporting.")

        # Step 3: Reporting (T026-T028)
        # Requires data/results/...
        if not run_pipeline_step("Reporting", run_reporting_phase, config):
            success = False
            logger.warning("Reporting failed.")

    except TimeoutError as e:
        logger.error(f"Pipeline terminated due to timeout: {e}")
        success = False
    except Exception as e:
        logger.critical(f"Unexpected pipeline failure: {e}", exc_info=True)
        success = False
    finally:
        clear_timeout()
        total_duration = time.time() - total_start
        
        # Log total execution time as per T007b
        logger.info(f"TOTAL_TIME: {total_duration}s")
        
        if success:
            logger.info("Pipeline completed successfully.")
        else:
            logger.warning("Pipeline completed with errors.")
        
        return success

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Code Churn vs Technical Debt Pipeline")
    parser.add_argument('--config', type=str, default=None, help='Path to config file (JSON/YAML)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Load config if provided, otherwise use defaults
    config = get_config_summary()
    if args.config:
        # Simple JSON load for now; expand if YAML support needed in config.py
        try:
            import json
            with open(args.config, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            logging.error(f"Failed to load config file: {e}")
    
    config['random_seed'] = args.seed
    
    success = run_pipeline(config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()