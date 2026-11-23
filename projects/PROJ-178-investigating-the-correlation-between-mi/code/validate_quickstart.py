import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from run_analysis import setup_logging, AnalysisTimer, run_pipeline
from config.environment import ensure_directories

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
LOG_FILE = project_root / "code" / "logs" / "runtime_validation.log"
QUICKSTART_PATH = project_root / "quickstart.md"

def run_step(step_name: str, func, *args, **kwargs):
    """Execute a step and record its duration."""
    logging.info(f"Starting step: {step_name}")
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logging.info(f"Completed step: {step_name} in {elapsed:.2f} seconds")
        return result, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"Step failed: {step_name} after {elapsed:.2f} seconds. Error: {e}")
        raise

def main():
    # Ensure directories exist
    ensure_directories()
    ensure_directories(project_root / "code" / "logs")

    # Setup logging to file and console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation (T045)")
    logger.info(f"Max allowed runtime: {MAX_RUNTIME_SECONDS} seconds (6 hours)")
    logger.info("=" * 60)

    total_start = time.time()
    steps_completed = []
    steps_failed = []

    try:
        # Step 1: Check quickstart.md exists
        if not QUICKSTART_PATH.exists():
            raise FileNotFoundError(f"quickstart.md not found at {QUICKSTART_PATH}")
        logger.info(f"Found quickstart.md at {QUICKSTART_PATH}")

        # Step 2: Run the pipeline (simulating the quickstart execution)
        # We assume the pipeline is defined in run_analysis.py
        # The run_pipeline function is the entry point for the full analysis
        logger.info("Executing full pipeline via run_analysis.run_pipeline()...")
        
        # Using a context manager for timer if available, or manual tracking
        # run_pipeline is expected to be the main entry point
        pipeline_result, pipeline_time = run_step(
            "Full Pipeline Execution",
            run_pipeline
        )
        steps_completed.append(("Full Pipeline", pipeline_time))

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        steps_failed.append(("Full Pipeline", str(e)))
    finally:
        total_elapsed = time.time() - total_start

    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total runtime: {total_elapsed:.2f} seconds ({total_elapsed/3600:.2f} hours)")
    logger.info(f"Max allowed: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600:.2f} hours)")

    if steps_failed:
        logger.error("FAILED STEPS:")
        for step, err in steps_failed:
            logger.error(f"  - {step}: {err}")
        logger.error("Validation FAILED due to execution errors.")
        sys.exit(1)

    if total_elapsed > MAX_RUNTIME_SECONDS:
        logger.error(f"Validation FAILED: Runtime ({total_elapsed:.2f}s) exceeds limit ({MAX_RUNTIME_SECONDS}s).")
        sys.exit(1)

    logger.info("SUCCESS: All steps completed within time limit.")
    logger.info("Runtime validation PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()