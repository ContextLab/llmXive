"""
Compute Resource Verification for T062.
Measures the runtime of the full pipeline, specifically the bootstrap step,
to ensure it completes within the 6-hour limit on a standard 2-core CPU.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from logger import get_logger
from main_pipeline import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "data" / "results" / "performance_report.log")
    ]
)
logger = get_logger("performance_benchmark")

RESULTS_DIR = PROJECT_ROOT / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = RESULTS_DIR / "performance_report.json"

def run_benchmark():
    """
    Executes the full pipeline and measures total runtime.
    """
    logger.info("="*60)
    logger.info("Starting Performance Benchmark (T062)")
    logger.info("="*60)
    
    start_time = time.time()
    pipeline_success = False
    error_msg = None
    
    try:
        logger.info("Invoking main_pipeline.run_pipeline()...")
        # This triggers the full flow: Ingestion -> Preprocessing -> 
        # Cohort -> Models (with 1000 bootstraps) -> Sensitivity -> Reporting
        run_pipeline()
        pipeline_success = True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pipeline execution failed: {error_msg}")
        logger.error(traceback.format_exc())
    finally:
        end_time = time.time()
        total_runtime_seconds = end_time - start_time
        total_runtime_hours = total_runtime_seconds / 3600.0

        logger.info("-"*60)
        logger.info(f"Benchmark Completed.")
        logger.info(f"Total Runtime: {total_runtime_seconds:.2f} seconds ({total_runtime_hours:.2f} hours)")
        logger.info(f"Success: {pipeline_success}")
        if not pipeline_success:
            logger.info(f"Error: {error_msg}")
        logger.info("-"*60)

        # Determine pass/fail based on the 6-hour limit
        LIMIT_HOURS = 6.0
        passed_limit = total_runtime_seconds <= (LIMIT_HOURS * 3600)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "task_id": "T062",
            "limit_hours": LIMIT_HOURS,
            "actual_runtime_seconds": total_runtime_seconds,
            "actual_runtime_hours": total_runtime_hours,
            "passed_time_limit": passed_limit,
            "pipeline_success": pipeline_success,
            "error_message": error_msg if not pipeline_success else None
        }

        # Save the report
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to: {REPORT_PATH}")

        if not pipeline_success:
            logger.error("CRITICAL: Pipeline failed. Verification cannot be marked complete without a successful run.")
            return False
        
        if not passed_limit:
            logger.warning(f"WARNING: Runtime exceeded 6-hour limit ({total_runtime_hours:.2f}h > {LIMIT_HOURS}h).")
            return False
        
        logger.info("SUCCESS: Pipeline completed within time limit.")
        return True

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
