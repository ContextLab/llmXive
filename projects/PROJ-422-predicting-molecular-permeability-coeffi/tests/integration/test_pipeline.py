"""
Integration test for the full training and evaluation flow (US2).

This test verifies the end-to-end pipeline:
1. Loads preprocessed data (train/test splits) from data/processed/
2. Trains GNN and Random Forest models via code/analysis/train.py
3. Evaluates models and computes metrics via code/analysis/evaluate.py
4. Performs statistical testing (t-test, Cohen's d, Power Analysis)
5. Verifies all required artifacts are generated in results/

Prerequisites:
- T017: Split data must exist at data/processed/train.csv and data/processed/test.csv
- T020, T021: Model definitions must be importable
- T022: Training infrastructure must be functional
- T024: Evaluation infrastructure must be functional
- T025: Statistical testing infrastructure must be functional
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging import setup_logging
from data.download import DataLoader
from data.preprocess import MoleculeProcessor
from data.split import execute_split
from analysis.train import main as train_main
from analysis.evaluate import main as evaluate_main
from analysis.statistical_tests import main as stats_main
from analysis.power_analysis import main as power_main

# Configure logging for the test
logger = setup_logging(
    log_level=logging.INFO,
    log_file=str(project_root / "results" / "integration_test_pipeline.log")
)

# Constants for test paths
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
DATA_INTERIM_DIR = project_root / "data" / "interim"
RESULTS_DIR = project_root / "results"
CONFIG_PATH = project_root / "config.yaml"

# Expected output artifacts
EXPECTED_ARTIFACTS = {
    "train.csv": DATA_PROCESSED_DIR / "train.csv",
    "test.csv": DATA_PROCESSED_DIR / "test.csv",
    "gnn_checkpoint.pt": DATA_INTERIM_DIR / "gnn_checkpoint.pt",
    "rf_checkpoint.pkl": DATA_INTERIM_DIR / "rf_checkpoint.pkl",
    "metrics.json": RESULTS_DIR / "metrics.json",
    "predictions_errors.json": RESULTS_DIR / "predictions_errors.json",
    "training_log.json": RESULTS_DIR / "training_log.json",
    "power_analysis.json": RESULTS_DIR / "power_analysis.json"
}

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    exists = path.exists()
    if exists:
        logger.info(f"✓ {description} exists: {path}")
        # Verify it's not empty
        if path.stat().st_size > 0:
            logger.info(f"  - Size: {path.stat().st_size} bytes")
            return True
        else:
            logger.error(f"  - ERROR: File is empty!")
            return False
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def validate_metrics_content(metrics_path: Path) -> bool:
    """Validate that metrics.json contains required fields."""
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        required_fields = ["model_metrics", "statistical_test", "power_analysis"]
        for field in required_fields:
            if field not in metrics:
                logger.error(f"Missing required field in metrics.json: {field}")
                return False
        
        # Check model metrics
        if "gnn" in metrics["model_metrics"]:
            gnn_metrics = metrics["model_metrics"]["gnn"]
            if not all(k in gnn_metrics for k in ["rmse", "mae", "r2"]):
                logger.error("GNN metrics missing required fields (rmse, mae, r2)")
                return False
        
        if "rf_baseline" in metrics["model_metrics"]:
            rf_metrics = metrics["model_metrics"]["rf_baseline"]
            if not all(k in rf_metrics for k in ["rmse", "mae", "r2"]):
                logger.error("RF metrics missing required fields (rmse, mae, r2)")
                return False
        
        # Check statistical test
        stats = metrics["statistical_test"]
        if not all(k in stats for k in ["p_value", "cohens_d", "confidence_interval"]):
            logger.error("Statistical test missing required fields")
            return False
        
        logger.info("✓ metrics.json contains all required fields and valid structure")
        return True
    except Exception as e:
        logger.error(f"Failed to validate metrics.json: {e}")
        return False

def run_integration_test():
    """Execute the full integration test pipeline."""
    logger.info("=" * 80)
    logger.info("STARTING INTEGRATION TEST: Full Training and Evaluation Flow")
    logger.info("=" * 80)
    
    # Ensure directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    all_passed = True
    
    # Step 1: Verify input data exists (from T017)
    logger.info("\n--- Step 1: Verifying Input Data ---")
    if not check_file_exists(EXPECTED_ARTIFACTS["train.csv"], "Training data"):
        logger.error("Training data missing. Please run T017 first.")
        return False
    if not check_file_exists(EXPECTED_ARTIFACTS["test.csv"], "Test data"):
        logger.error("Test data missing. Please run T017 first.")
        return False
    
    # Step 2: Run Training (T022)
    logger.info("\n--- Step 2: Running Training Pipeline ---")
    try:
        logger.info("Invoking analysis.train.main()...")
        # Note: In a real scenario, we might need to pass arguments or set up config
        # For now, we assume the main function handles its own configuration
        train_main()
        logger.info("Training completed successfully.")
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        all_passed = False
    
    # Verify training outputs
    logger.info("\n--- Verifying Training Outputs ---")
    if not check_file_exists(EXPECTED_ARTIFACTS["gnn_checkpoint.pt"], "GNN Checkpoint"):
        all_passed = False
    if not check_file_exists(EXPECTED_ARTIFACTS["rf_checkpoint.pkl"], "RF Checkpoint"):
        all_passed = False
    if not check_file_exists(EXPECTED_ARTIFACTS["training_log.json"], "Training Log"):
        all_passed = False
    
    # Step 3: Run Evaluation (T024)
    logger.info("\n--- Step 3: Running Evaluation Pipeline ---")
    try:
        logger.info("Invoking analysis.evaluate.main()...")
        evaluate_main()
        logger.info("Evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        all_passed = False
    
    # Verify evaluation outputs
    logger.info("\n--- Verifying Evaluation Outputs ---")
    if not check_file_exists(EXPECTED_ARTIFACTS["metrics.json"], "Metrics JSON"):
        all_passed = False
    if not check_file_exists(EXPECTED_ARTIFACTS["predictions_errors.json"], "Predictions Errors"):
        all_passed = False
    
    # Step 4: Run Statistical Tests (T025)
    logger.info("\n--- Step 4: Running Statistical Tests ---")
    try:
        logger.info("Invoking analysis.statistical_tests.main()...")
        stats_main()
        logger.info("Statistical tests completed successfully.")
    except Exception as e:
        logger.error(f"Statistical tests failed: {e}", exc_info=True)
        all_passed = False
    
    # Step 5: Run Power Analysis (T025b)
    logger.info("\n--- Step 5: Running Power Analysis ---")
    try:
        logger.info("Invoking analysis.power_analysis.main()...")
        power_main()
        logger.info("Power analysis completed successfully.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        all_passed = False
    
    # Verify power analysis output
    if not check_file_exists(EXPECTED_ARTIFACTS["power_analysis.json"], "Power Analysis JSON"):
        all_passed = False
    
    # Final Validation
    logger.info("\n--- Final Validation ---")
    if check_file_exists(EXPECTED_ARTIFACTS["metrics.json"], "Final Metrics"):
        if not validate_metrics_content(EXPECTED_ARTIFACTS["metrics.json"]):
            all_passed = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("INTEGRATION TEST PASSED: All artifacts generated and validated.")
    else:
        logger.error("INTEGRATION TEST FAILED: Some checks did not pass.")
    logger.info("=" * 80)
    
    return all_passed

def main():
    """Main entry point for the integration test."""
    success = run_integration_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()