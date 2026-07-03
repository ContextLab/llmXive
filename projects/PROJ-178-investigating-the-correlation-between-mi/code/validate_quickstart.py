"""
T045: Quickstart Validation Script

This script validates the entire pipeline by executing the quickstart workflow
and verifying that the total runtime does not exceed 6 hours (21,600 seconds)
on a 2 CPU runner.

It executes the following steps:
1. Setup directories (via environment config)
2. Run data acquisition (load_data)
3. Run preprocessing (preprocess)
4. Run metadata merge (merge_metadata)
5. Run cleaning (clean_dataset)
6. Run statistical modeling (model)
7. Run sensitivity analysis (sensitivity)
8. Run visualization (visualize)
9. Generate summary (summarize_results)

The script measures wall-clock time and exits with a non-zero status if
the total time exceeds the 6-hour threshold.
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config.environment import ensure_directories
from analysis.load_data import main as load_data_main
from analysis.preprocess import main as preprocess_main
from analysis.merge_metadata import main as merge_metadata_main
from analysis.clean_dataset import main as clean_dataset_main
from analysis.model import main as model_main
from analysis.sensitivity import main as sensitivity_main
from analysis.visualize import main as visualize_main
from analysis.summarize_results import main as summarize_results_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "code" / "logs" / "quickstart_validation.log")
    ]
)
logger = logging.getLogger(__name__)

MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours

def run_step(step_name, func):
    """Run a pipeline step and log its duration."""
    logger.info(f"Starting step: {step_name}")
    start = time.time()
    try:
        func()
        duration = time.time() - start
        logger.info(f"Completed step: {step_name} in {duration:.2f} seconds")
        return duration
    except Exception as e:
        duration = time.time() - start
        logger.error(f"Failed step: {step_name} after {duration:.2f} seconds: {e}")
        raise

def main():
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T045)")
    logger.info(f"Max allowed runtime: {MAX_RUNTIME_SECONDS} seconds (6 hours)")
    logger.info("=" * 60)

    total_start = time.time()
    steps_completed = []

    try:
        # 1. Ensure directories exist
        logger.info("Step 1: Ensuring directories...")
        ensure_directories()
        steps_completed.append("directories")

        # 2. Data Acquisition
        steps_completed.append("load_data")
        run_step("Data Acquisition (load_data)", load_data_main)

        # 3. Preprocessing
        steps_completed.append("preprocess")
        run_step("Preprocessing (preprocess)", preprocess_main)

        # 4. Metadata Merge
        steps_completed.append("merge_metadata")
        run_step("Metadata Merge (merge_metadata)", merge_metadata_main)

        # 5. Clean Dataset
        steps_completed.append("clean_dataset")
        run_step("Clean Dataset (clean_dataset)", clean_dataset_main)

        # 6. Statistical Modeling
        steps_completed.append("model")
        run_step("Statistical Modeling (model)", model_main)

        # 7. Sensitivity Analysis
        steps_completed.append("sensitivity")
        run_step("Sensitivity Analysis (sensitivity)", sensitivity_main)

        # 8. Visualization
        steps_completed.append("visualize")
        run_step("Visualization (visualize)", visualize_main)

        # 9. Summarize Results
        steps_completed.append("summarize_results")
        run_step("Summarize Results (summarize_results)", summarize_results_main)

    except Exception as e:
        total_duration = time.time() - total_start
        logger.error(f"Validation FAILED at step '{steps_completed[-1] if steps_completed else 'unknown'}' after {total_duration:.2f}s")
        logger.error(f"Error: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        sys.exit(1)

    total_duration = time.time() - total_start
    
    logger.info("=" * 60)
    logger.info("Quickstart Validation Summary")
    logger.info("=" * 60)
    logger.info(f"Steps completed: {', '.join(steps_completed)}")
    logger.info(f"Total runtime: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
    logger.info(f"Max allowed runtime: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS/3600:.2f} hours)")

    if total_duration > MAX_RUNTIME_SECONDS:
        logger.error(f"❌ VALIDATION FAILED: Runtime exceeded 6-hour limit by {total_duration - MAX_RUNTIME_SECONDS:.2f} seconds.")
        print(f"\n❌ VALIDATION FAILED: Total runtime ({total_duration:.2f}s) exceeded limit ({MAX_RUNTIME_SECONDS}s).")
        sys.exit(1)
    else:
        logger.info("✅ VALIDATION PASSED: Total runtime is within the 6-hour limit.")
        print(f"\n✅ VALIDATION PASSED: Total runtime ({total_duration:.2f}s) is within the 6-hour limit.")
        sys.exit(0)

if __name__ == "__main__":
    main()