"""
T042: Validate pipeline execution time against a defined operational threshold.

This script measures the end-to-end execution time of the pipeline and compares
it against a configurable threshold to ensure operational latency requirements
are met.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.pipeline_runner import run_pipeline
from code.logging_config import setup_logging, get_logger

# Configuration
PERFORMANCE_THRESHOLD_SECONDS = 300  # 5 minutes default threshold
OUTPUT_FILE = "data/processed/performance_validation.json"
LOG_FILE = "data/outputs/performance_validation.log"

def setup_performance_logging():
    """Setup logging for performance validation."""
    log_path = project_root / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("performance_validator")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def validate_pipeline_performance():
    """
    Execute the pipeline and validate execution time against threshold.
    
    Returns:
        dict: Validation results including timing, threshold, and pass/fail status.
    """
    logger = setup_performance_logging()
    logger.info("Starting pipeline performance validation...")
    logger.info(f"Threshold set to {PERFORMANCE_THRESHOLD_SECONDS} seconds")
    
    start_time = time.time()
    execution_success = False
    error_message = None
    
    try:
        # Run the full pipeline
        logger.info("Executing pipeline...")
        pipeline_result = run_pipeline()
        
        if pipeline_result.get("status") != "success":
            error_message = pipeline_result.get("error", "Unknown pipeline error")
            logger.error(f"Pipeline execution failed: {error_message}")
        else:
            execution_success = True
            logger.info("Pipeline execution completed successfully")
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Pipeline execution raised exception: {error_message}", exc_info=True)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    logger.info(f"Total execution time: {total_duration:.2f} seconds")
    
    # Determine pass/fail status
    passed = execution_success and (total_duration <= PERFORMANCE_THRESHOLD_SECONDS)
    
    # Prepare results
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution_success": execution_success,
        "total_duration_seconds": round(total_duration, 2),
        "threshold_seconds": PERFORMANCE_THRESHOLD_SECONDS,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "error_message": error_message,
        "details": {
            "pipeline_status": pipeline_result.get("status", "error") if not execution_success else "success",
            "threshold_met": total_duration <= PERFORMANCE_THRESHOLD_SECONDS
        }
    }
    
    # Save results to file
    output_path = project_root / OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Performance validation results saved to {OUTPUT_FILE}")
    logger.info(f"Validation status: {results['status']}")
    
    if not passed:
        if not execution_success:
            logger.error("VALIDATION FAILED: Pipeline did not execute successfully")
        else:
            logger.error(f"VALIDATION FAILED: Execution time ({total_duration:.2f}s) exceeded threshold ({PERFORMANCE_THRESHOLD_SECONDS}s)")
    else:
        logger.info("VALIDATION PASSED: Pipeline executed successfully within threshold")
    
    return results

def main():
    """Main entry point for performance validation."""
    results = validate_pipeline_performance()
    
    # Exit with appropriate code
    sys.exit(0 if results["passed"] else 1)

if __name__ == "__main__":
    main()
