"""
Task T036: Performance optimization verification.

Verifies that the full parameter sweep completes within the 6-hour budget.
Records execution time and metrics to state/sweep_timing.log.

This script acts as a wrapper/validator around the existing threshold sweep
orchestrator (threshold_sweep.py) to measure and log the total runtime.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.threshold_sweep import main as run_threshold_sweep
from utils.config import get_project_paths, ensure_directories

# Constants
TIME_BUDGET_SECONDS = 6 * 60 * 60  # 6 hours
OUTPUT_FILE = "state/sweep_timing.log"

def setup_logging():
    """Configure logging to file and console."""
    paths = get_project_paths()
    ensure_directories()
    
    log_file = paths["state"] / OUTPUT_FILE
    
    # Create logger
    logger = logging.getLogger("sweep_timing")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger, log_file

def main():
    """
    Execute the full parameter sweep with timing instrumentation.
    
    Runs the threshold sweep, measures total execution time, and logs
    whether it completed within the 6-hour budget.
    """
    logger, log_path = setup_logging()
    
    logger.info("=" * 80)
    logger.info("TASK T036: Performance Optimization Verification")
    logger.info("=" * 80)
    logger.info(f"Time Budget: {TIME_BUDGET_SECONDS} seconds (6 hours)")
    logger.info(f"Start Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("-" * 80)
    
    start_time = time.time()
    success = False
    error_msg = None
    
    try:
        logger.info("Starting full parameter sweep (threshold_sweep.py)...")
        logger.info("This may take several minutes depending on matrix sizes and seeds.")
        
        # Execute the threshold sweep
        # The sweep orchestrator handles the full parameter grid defined in T040a
        run_threshold_sweep()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("-" * 80)
        logger.info("Sweep completed successfully.")
        logger.info(f"End Time: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"Total Duration: {duration:.2f} seconds ({duration/3600:.2f} hours)")
        
        if duration <= TIME_BUDGET_SECONDS:
            logger.info("STATUS: PASSED - Within 6-hour budget.")
            success = True
        else:
            logger.warning("STATUS: FAILED - Exceeded 6-hour budget.")
            success = False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        error_msg = str(e)
        
        logger.error("-" * 80)
        logger.error("Sweep execution failed with exception.")
        logger.error(f"End Time: {datetime.now(timezone.utc).isoformat()}")
        logger.error(f"Duration at failure: {duration:.2f} seconds")
        logger.error(f"Error: {error_msg}")
        logger.error("STATUS: FAILED - Execution error.")
        success = False
    
    # Write summary to log file (already done via logging, but ensure final record)
    logger.info("=" * 80)
    logger.info("FINAL RESULT")
    logger.info("=" * 80)
    logger.info(f"Success: {success}")
    logger.info(f"Duration: {duration:.2f} seconds")
    if error_msg:
        logger.error(f"Error Message: {error_msg}")
    logger.info("=" * 80)
    
    # Also write a JSON summary for programmatic access
    summary = {
        "task_id": "T036",
        "start_time": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
        "end_time": datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(),
        "duration_seconds": duration,
        "time_budget_seconds": TIME_BUDGET_SECONDS,
        "within_budget": success,
        "status": "passed" if success else "failed",
        "error": error_msg
    }
    
    summary_path = project_root / "state" / "sweep_timing_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary written to: {summary_path}")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
