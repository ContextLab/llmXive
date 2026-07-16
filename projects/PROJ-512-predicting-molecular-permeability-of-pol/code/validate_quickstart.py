"""
Quickstart Validation Script for PROJ-512
Executes the steps defined in quickstart.md to verify the pipeline functions correctly.
"""
import os
import sys
import logging
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.utils import setup_logging, set_seed, get_seed
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from models.baselines import main as baselines_main
from models.trainer import main as trainer_main
from evaluation.report import main as report_main

# Configure logging
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_file_exists(path_str: str, description: str) -> bool:
    path = project_root / path_str
    if not path.exists():
        logger.error(f"FAIL: {description} not found at {path}")
        return False
    logger.info(f"PASS: {description} exists at {path}")
    return True

def run_step(step_name: str, func, *args, **kwargs) -> bool:
    logger.info(f"--- Executing: {step_name} ---")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"SUCCESS: {step_name} completed in {elapsed:.2f}s")
        return True
    except Exception as e:
        logger.error(f"FAIL: {step_name} raised {type(e).__name__}: {e}")
        return False

def main():
    logger.info("Starting Quickstart Validation for PROJ-512")
    
    # 1. Setup & Environment Check
    logger.info("Step 1: Environment & Seed Setup")
    set_seed(42)
    logger.info(f"Seed initialized: {get_seed()}")

    # 2. Data Ingestion
    # Note: ingestion_main handles its own internal logic and file generation
    if not run_step("Data Ingestion", ingestion_main):
        logger.error("Quickstart validation FAILED at Data Ingestion.")
        return 1

    # 3. Preprocessing (Scaffold Split & Feature Extraction)
    if not run_step("Preprocessing", preprocessing_main):
        logger.error("Quickstart validation FAILED at Preprocessing.")
        return 1

    # 4. Baseline Models
    if not run_step("Baseline Models (RF & Linear)", baselines_main):
        logger.error("Quickstart validation FAILED at Baseline Models.")
        return 1

    # 5. GNN Training
    if not run_step("GNN Training", trainer_main):
        logger.error("Quickstart validation FAILED at GNN Training.")
        return 1

    # 6. Evaluation & Reporting
    if not run_step("Evaluation & Reporting", report_main):
        logger.error("Quickstart validation FAILED at Evaluation.")
        return 1

    # 7. Verify Final Artifacts
    logger.info("Step 7: Verifying Final Artifacts")
    artifacts = [
        ("code/data/processed/polymers.h5", "Processed HDF5 Dataset"),
        ("code/data/processed/splits.json", "Scaffold Split Indices"),
        ("code/models/checkpoints/best_gnn.pt", "Best GNN Checkpoint"),
        ("code/evaluation/results/baseline_metrics.json", "Baseline Metrics"),
        ("code/evaluation/results/gnn_metrics.json", "GNN Metrics"),
        ("code/evaluation/results/final_report.json", "Final Statistical Report"),
    ]

    all_present = True
    for path_str, desc in artifacts:
        if not check_file_exists(path_str, desc):
            all_present = False

    if not all_present:
        logger.error("Quickstart validation FAILED: Missing required artifacts.")
        return 1

    logger.info("========================================")
    logger.info("Quickstart Validation: PASSED")
    logger.info("All pipeline stages executed successfully.")
    logger.info("All required artifacts generated.")
    logger.info("========================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())