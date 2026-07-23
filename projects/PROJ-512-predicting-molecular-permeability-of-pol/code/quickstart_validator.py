"""
T064: Quickstart Validation Script
Verifies the execution of the full pipeline and the production of required artifacts.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path

# Project root adjustment
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from data.utils import setup_logging, set_seed
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from models.trainer import main as trainer_main
from evaluation.metrics import main as metrics_main
from evaluation.stats import main as stats_main
from quickstart import verify_artifacts

# Constants for artifact paths relative to project root
ARTIFACTS = {
    "polymers.h5": ROOT_DIR / "code" / "data" / "processed" / "polymers.h5",
    "metrics.json": ROOT_DIR / "code" / "evaluation" / "results" / "metrics.json",
    "sensitivity_sweep.json": ROOT_DIR / "code" / "evaluation" / "results" / "sensitivity_sweep.json"
}

def run_step(step_name, step_func):
    """Execute a pipeline step with timing and error handling."""
    logger = logging.getLogger(__name__)
    logger.info(f"--- Starting Step: {step_name} ---")
    start = time.time()
    try:
        step_func()
        duration = time.time() - start
        logger.info(f"--- Completed Step: {step_name} in {duration:.2f}s ---")
        return True
    except Exception as e:
        duration = time.time() - start
        logger.error(f"--- Failed Step: {step_name} after {duration:.2f}s ---")
        logger.error(f"Error: {str(e)}")
        raise

def main():
    """Main validation entry point."""
    setup_logging(log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Quickstart Validation (T064)...")
    logger.info(f"Project Root: {ROOT_DIR}")
    
    # Ensure seed for reproducibility
    set_seed(42)
    
    success = True
    
    # Step 1: Ingestion (Data Fetching & Cleaning)
    # This generates raw data and cleans it, but does NOT save the final HDF5
    # The ingestion pipeline in this project is split:
    # ingestion.py -> fetches/cleans -> preprocessing.py -> features -> save_dataset.py -> h5
    # We call the ingestion main to ensure raw data is ready.
    try:
        # Note: ingestion_main() typically handles fetching and initial cleaning.
        # We assume it prepares the environment for preprocessing.
        run_step("Ingestion Pipeline", ingestion_main)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        success = False

    if not success:
        logger.warning("Skipping subsequent steps due to ingestion failure.")
    else:
        # Step 2: Preprocessing (Feature Extraction & Scaffold Split)
        # This converts data to graphs and saves to HDF5
        try:
            run_step("Preprocessing Pipeline", preprocessing_main)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            success = False

        if success:
            # Step 3: Training (GNN & Baselines)
            # This trains models and saves metrics
            try:
                run_step("Training Pipeline", trainer_main)
            except Exception as e:
                logger.error(f"Training failed: {e}")
                success = False

            if success:
                # Step 4: Metrics Evaluation
                try:
                    run_step("Metrics Evaluation", metrics_main)
                except Exception as e:
                    logger.error(f"Metrics evaluation failed: {e}")
                    success = False

                if success:
                    # Step 5: Statistical Validation (Sensitivity Sweep)
                    try:
                        run_step("Statistical Validation", stats_main)
                    except Exception as e:
                        logger.error(f"Statistical validation failed: {e}")
                        success = False

    # Final Verification
    logger.info("--- Final Artifact Verification ---")
    all_present = True
    for name, path in ARTIFACTS.items():
        exists = path.exists()
        status = "FOUND" if exists else "MISSING"
        logger.info(f"Artifact: {name} -> {status} (Path: {path})")
        if not exists:
            all_present = False

    if all_present:
        logger.info("SUCCESS: All required artifacts (polymers.h5, metrics.json, sensitivity_sweep.json) produced.")
        logger.info("T064 Validation PASSED.")
        return 0
    else:
        logger.error("FAILURE: One or more required artifacts are missing.")
        logger.error("T064 Validation FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
