"""
Validation script to verify that the pipeline artifacts exist and are correct.
This script is invoked by the quickstart run-book to ensure reproducibility.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Define paths
FEATURES_PATH = project_root / "data" / "processed" / "features.csv"
METRICS_PATH = project_root / "results" / "metrics.json"
MODEL_PATH = project_root / "results" / "model.pkl"
CANDIDATES_PATH = project_root / "results" / "screening_candidates.md"

def validate_artifacts():
    """Validate that all required artifacts exist."""
    logger.info("Validating artifacts...")
    errors = []

    if not FEATURES_PATH.exists():
        errors.append(f"Missing required artifact: {FEATURES_PATH}")
    else:
        logger.info(f"Found {FEATURES_PATH}")
        # Verify decomposition_energy has no nulls
        import pandas as pd
        df = pd.read_csv(FEATURES_PATH)
        if df['decomposition_energy'].isnull().sum() > 0:
            errors.append(f"Target column 'decomposition_energy' has nulls in {FEATURES_PATH}")
        else:
            logger.info("PASS: Zero nulls in target column 'decomposition_energy'")

    if not METRICS_PATH.exists():
        errors.append(f"Missing required artifact: {METRICS_PATH}")
    else:
        logger.info(f"Found {METRICS_PATH}")
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
            required_keys = ['test_rmse', 'best_params', 'dft_functional']
            for key in required_keys:
                if key not in metrics:
                    errors.append(f"Missing key '{key}' in {METRICS_PATH}")
                else:
                    logger.info(f"Found key '{key}' in {METRICS_PATH}")

    if not MODEL_PATH.exists():
        errors.append(f"Missing required artifact: {MODEL_PATH}")
    else:
        logger.info(f"Found {MODEL_PATH}")

    if not CANDIDATES_PATH.exists():
        errors.append(f"Missing required artifact: {CANDIDATES_PATH}")
    else:
        logger.info(f"Found {CANDIDATES_PATH}")

    return errors

def validate_metrics():
    """Validate that metrics meet the required thresholds."""
    logger.info("Validating metrics...")
    errors = []

    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
            test_rmse = metrics.get('test_rmse')
            if test_rmse is not None:
                if test_rmse > 0.15:
                    errors.append(f"Test RMSE ({test_rmse}) exceeds threshold of 0.15 eV/atom")
                else:
                    logger.info(f"PASS: Test RMSE ({test_rmse}) is within threshold")
            else:
                errors.append("Test RMSE not found in metrics")
    else:
        errors.append(f"Cannot validate metrics: {METRICS_PATH} not found")

    return errors

def main():
    """Main entry point for validation."""
    logger.info("Starting artifact and metrics validation...")
    start_time = time.time()

    artifact_errors = validate_artifacts()
    metric_errors = validate_metrics()

    end_time = time.time()
    duration = end_time - start_time

    all_errors = artifact_errors + metric_errors

    if all_errors:
        logger.error(f"Validation FAILED with {len(all_errors)} errors:")
        for err in all_errors:
            logger.error(f"  - {err}")
        log_pipeline_event(f"Validation failed in {duration:.2f} seconds")
        sys.exit(1)
    else:
        logger.info("Validation PASSED successfully.")
        log_pipeline_event(f"Validation passed in {duration:.2f} seconds")
        sys.exit(0)

if __name__ == "__main__":
    main()