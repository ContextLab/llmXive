import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from sibling modules using the exact API surface provided
from training import run_training_pipeline, main as training_main
from evaluation import run_evaluation_pipeline, main as evaluation_main
from utils import setup_logging, get_env_var

# Constants
MAX_EXECUTION_TIME_HOURS = 6
MAX_EXECUTION_TIME_SECONDS = MAX_EXECUTION_TIME_HOURS * 3600
OUTPUT_DIR = project_root / "results" / "metrics"
TIMING_REPORT_FILE = OUTPUT_DIR / "timing_verification.json"

logger = logging.getLogger(__name__)

def run_timed_training() -> Dict[str, Any]:
    """
    Executes the training pipeline and measures execution time.
    Returns a dictionary with timing metrics and status.
    """
    logger.info("Starting timed training pipeline execution...")
    start_time = time.perf_counter()
    
    try:
        # Run the training pipeline (this loads data, trains model, saves artifacts)
        # We call run_training_pipeline directly. 
        # Note: run_training_pipeline is expected to handle its own logging and data paths.
        training_result = run_training_pipeline()
        
        end_time = time.perf_counter()
        duration_seconds = end_time - start_time
        
        return {
            "status": "success",
            "duration_seconds": duration_seconds,
            "duration_hours": duration_seconds / 3600,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
            "result": training_result
        }
    except Exception as e:
        end_time = time.perf_counter()
        duration_seconds = end_time - start_time
        logger.error(f"Training pipeline failed after {duration_seconds:.2f} seconds: {e}")
        return {
            "status": "failed",
            "duration_seconds": duration_seconds,
            "duration_hours": duration_seconds / 3600,
            "error": str(e),
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        }

def run_timed_evaluation() -> Dict[str, Any]:
    """
    Executes the evaluation pipeline and measures execution time.
    Returns a dictionary with timing metrics and status.
    """
    logger.info("Starting timed evaluation pipeline execution...")
    start_time = time.perf_counter()
    
    try:
        # Run the evaluation pipeline (loads model, computes metrics, generates plots)
        evaluation_result = run_evaluation_pipeline()
        
        end_time = time.perf_counter()
        duration_seconds = end_time - start_time
        
        return {
            "status": "success",
            "duration_seconds": duration_seconds,
            "duration_hours": duration_seconds / 3600,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
            "result": evaluation_result
        }
    except Exception as e:
        end_time = time.perf_counter()
        duration_seconds = end_time - start_time
        logger.error(f"Evaluation pipeline failed after {duration_seconds:.2f} seconds: {e}")
        return {
            "status": "failed",
            "duration_seconds": duration_seconds,
            "duration_hours": duration_seconds / 3600,
            "error": str(e),
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        }

def main():
    """
    Main entry point for T030: Verify execution time of full training/eval cycle.
    Runs training and evaluation, measures total time, and writes a report.
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    log_file = project_root / "results" / "metrics" / "timing_verification.log"
    setup_logging(log_file=str(log_file), level=logging.INFO)
    
    logger.info("=" * 60)
    logger.info("T030: Timing Verification for Training/Evaluation Cycle")
    logger.info(f"Max allowed time: {MAX_EXECUTION_TIME_HOURS} hours ({MAX_EXECUTION_TIME_SECONDS} seconds)")
    logger.info("=" * 60)
    
    # Run training
    training_metrics = run_timed_training()
    
    # Run evaluation
    evaluation_metrics = run_timed_evaluation()
    
    # Calculate total time
    total_seconds = training_metrics["duration_seconds"] + evaluation_metrics["duration_seconds"]
    total_hours = total_seconds / 3600
    is_within_limit = total_seconds <= MAX_EXECUTION_TIME_SECONDS
    
    # Construct final report
    report = {
        "task_id": "T030",
        "max_allowed_hours": MAX_EXECUTION_TIME_HOURS,
        "max_allowed_seconds": MAX_EXECUTION_TIME_SECONDS,
        "total_execution_seconds": total_seconds,
        "total_execution_hours": total_hours,
        "within_limit": is_within_limit,
        "training": training_metrics,
        "evaluation": evaluation_metrics,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    
    # Write report to disk
    with open(TIMING_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info("-" * 60)
    logger.info(f"Total Execution Time: {total_hours:.4f} hours ({total_seconds:.2f} seconds)")
    logger.info(f"Within Limit ({MAX_EXECUTION_TIME_HOURS}h): {'YES' if is_within_limit else 'NO'}")
    logger.info(f"Report saved to: {TIMING_REPORT_FILE}")
    logger.info("-" * 60)
    
    if not is_within_limit:
        logger.warning("EXECUTION TIME EXCEEDED LIMIT. Task T030 verification failed.")
        # Do not raise, as the script successfully ran and recorded the time.
        # The verification result is in the JSON report.
    else:
        logger.info("EXECUTION TIME WITHIN LIMIT. Task T030 verification passed.")
    
    return 0 if is_within_limit else 1

if __name__ == "__main__":
    # Ensure we are in the code directory or have correct paths
    sys.exit(main())
