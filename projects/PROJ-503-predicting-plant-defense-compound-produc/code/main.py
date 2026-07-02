"""
Main entry point for the plant defense compound prediction pipeline.
Implements CI resource monitoring with a 4-hour CPU time limit per FR-008.
"""
import sys
import time
import resource
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from exceptions import E_TIMEOUT
from error_handler import raise_timeout_error, handle_error
from logging_utils import get_pairing_log_stats, get_filtering_log_stats

# Constants
MAX_CPU_TIME_SECONDS = 4 * 3600  # 4 hours in seconds
LOG_FILE = project_root / "logs" / "pipeline_execution.log"

def setup_logging():
    """Configure logging to file and console."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_elapsed_cpu_time():
    """
    Get the elapsed CPU time in seconds for the current process.
    Uses resource.getrusage to get user + system CPU time.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime

def check_and_log_cpu_time(logger):
    """
    Check if elapsed CPU time exceeds the limit.
    Logs the current elapsed time and raises E-TIMEOUT if exceeded.
    """
    elapsed = get_elapsed_cpu_time()
    logger.info(f"Elapsed CPU time: {elapsed:.2f} seconds ({elapsed/3600:.2f} hours)")
    
    if elapsed > MAX_CPU_TIME_SECONDS:
        logger.error(f"CPU time limit exceeded: {elapsed:.2f}s > {MAX_CPU_TIME_SECONDS}s")
        raise_timeout_error(
            logger,
            f"Pipeline exceeded maximum CPU time limit of {MAX_CPU_TIME_SECONDS/3600} hours. "
            f"Elapsed: {elapsed:.2f} seconds."
        )

def run_pipeline():
    """
    Main pipeline execution logic.
    Currently a placeholder for the actual pipeline steps.
    Includes the required timeout monitoring.
    """
    logger = setup_logging()
    logger.info("Starting plant defense compound prediction pipeline...")
    
    try:
        # Initial check
        check_and_log_cpu_time(logger)
        
        # TODO: Insert actual pipeline steps here
        # e.g., data download, preprocessing, modeling
        # Each step should call check_and_log_cpu_time(logger) periodically
        
        logger.info("Pipeline execution completed successfully.")
        
        # Final check
        check_and_log_cpu_time(logger)
        
    except E_TIMEOUT as e:
        logger.critical(f"Pipeline aborted due to timeout: {e}")
        raise
    except Exception as e:
        handle_error(logger, e)
        raise

def main():
    """Entry point for the script."""
    run_pipeline()

if __name__ == "__main__":
    main()