"""
Integration test to run the full pipeline, capture execution time,
and log the specific duration value for SC-005 verification.

This script:
1. Runs the full data pipeline (T019) and model evaluation (T025).
2. Captures the total wall-clock time.
3. Logs the duration to stdout and `logs/runtime.log`.
4. Asserts duration < 6 hours (21600 seconds).
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path to import src modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.pipeline import run_data_pipeline
from src.models.main_eval import run_evaluation

# Configure logging
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "runtime.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='w')
    ]
)

logger = logging.getLogger(__name__)

MAX_DURATION_SECONDS = 6 * 3600  # 6 hours

def main():
    logger.info("=" * 60)
    logger.info("Starting Full Pipeline Integration Test (T031)")
    logger.info("=" * 60)

    start_time = time.time()
    start_dt = datetime.now()
    logger.info(f"Start time: {start_dt.isoformat()}")

    try:
        # Step 1: Run Data Pipeline (T019)
        logger.info("Step 1: Executing Data Pipeline (T019)...")
        # Assuming run_data_pipeline returns the path to the processed CSV or None on success
        processed_csv_path = run_data_pipeline()
        
        if processed_csv_path is None:
            logger.error("Data pipeline failed to produce a valid CSV.")
            sys.exit(1)
        
        logger.info(f"Data pipeline completed. Output: {processed_csv_path}")

        # Step 2: Run Model Evaluation (T025)
        logger.info("Step 2: Executing Model Evaluation (T025)...")
        # Assuming run_evaluation runs the training and evaluation
        eval_success = run_evaluation()
        
        if not eval_success:
            logger.error("Model evaluation failed.")
            sys.exit(1)

        logger.info("Model evaluation completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}", exc_info=True)
        sys.exit(1)

    end_time = time.time()
    end_dt = datetime.now()
    duration_seconds = end_time - start_time

    logger.info("=" * 60)
    logger.info("Pipeline Execution Summary")
    logger.info("=" * 60)
    logger.info(f"Start: {start_dt.isoformat()}")
    logger.info(f"End:   {end_dt.isoformat()}")
    logger.info(f"Total Duration: {duration_seconds:.2f} seconds ({duration_seconds/3600:.2f} hours)")
    logger.info("=" * 60)

    # SC-005 Verification: Log specific duration value
    logger.info(f"SC-005_MEASURED_DURATION_SECONDS: {duration_seconds:.6f}")

    # Assertion: Duration < 6 hours
    if duration_seconds >= MAX_DURATION_SECONDS:
        logger.error(f"FAIL: Pipeline duration ({duration_seconds:.2f}s) exceeded limit ({MAX_DURATION_SECONDS}s).")
        sys.exit(1)
    else:
        logger.info(f"PASS: Pipeline duration ({duration_seconds:.2f}s) is within limit (< {MAX_DURATION_SECONDS}s).")

    logger.info("Integration test T031 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
