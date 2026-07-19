import os
import sys
import logging
import json
import time
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data.utils import setup_logging, set_seed
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.save_dataset import main as save_dataset_main
from models.trainer import main as trainer_main
from evaluation.metrics import main as metrics_main
from evaluation.stats import main as stats_main
from evaluation.report import main as report_main

logger = logging.getLogger(__name__)

REQUIRED_ARTIFACTS = [
    "data/processed/polymers.h5",
    "data/processed/scaffold_split_indices.json",
    "evaluation/results/metrics.json",
    "evaluation/results/sensitivity_sweep.json",
    "evaluation/results/final_report.json"
]

def check_file_exists(path_str: str) -> bool:
    """Check if a file exists at the given relative path."""
    full_path = code_root / path_str
    exists = full_path.exists()
    status = "FOUND" if exists else "MISSING"
    logger.info(f"Artifact check [{status}]: {path_str}")
    return exists

def run_step(step_name: str, func, *args, **kwargs) -> bool:
    """Run a pipeline step and return success status."""
    logger.info(f"Starting step: {step_name}")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Step {step_name} completed successfully in {duration:.2f}s")
        return True
    except Exception as e:
        logger.error(f"Step {step_name} failed: {e}")
        raise

def main():
    """
    Execute the full quickstart validation pipeline.
    This script runs the entire pipeline end-to-end to verify:
    1. Data ingestion and simulation generation (if needed)
    2. Graph construction and preprocessing
    3. Model training and baseline comparison
    4. Statistical validation
    5. Report generation
    
    Finally, it verifies the existence of required output artifacts.
    """
    setup_logging(log_level=logging.INFO)
    set_seed(42)

    logger.info("="*60)
    logger.info("Starting Quickstart Validation Pipeline (T064)")
    logger.info("="*60)

    success = True

    try:
        # Step 1: Data Ingestion
        run_step("Data Ingestion", ingestion_main)

        # Step 2: Preprocessing (Feature Extraction & Split)
        run_step("Preprocessing", preprocessing_main)

        # Step 3: Save Processed Dataset
        run_step("Save Dataset", save_dataset_main)

        # Step 4: Model Training
        run_step("Model Training", trainer_main)

        # Step 5: Metrics Calculation
        run_step("Metrics Calculation", metrics_main)

        # Step 6: Statistical Analysis
        run_step("Statistical Analysis", stats_main)

        # Step 7: Report Generation
        run_step("Report Generation", report_main)

        logger.info("="*60)
        logger.info("Pipeline Execution Complete. Verifying Artifacts...")
        logger.info("="*60)

        missing_files = []
        for artifact in REQUIRED_ARTIFACTS:
            if not check_file_exists(artifact):
                missing_files.append(artifact)

        if missing_files:
            logger.error(f"Validation FAILED. Missing {len(missing_files)} artifacts:")
            for f in missing_files:
                logger.error(f"  - {f}")
            success = False
        else:
            logger.info("Validation PASSED. All required artifacts present.")

    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        success = False

    if success:
        logger.info("Quickstart validation completed successfully.")
        return 0
    else:
        logger.error("Quickstart validation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())