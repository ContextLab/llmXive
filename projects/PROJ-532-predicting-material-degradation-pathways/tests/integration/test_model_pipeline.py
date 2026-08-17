"""
Integration test for the training and evaluation pipeline (User Story 2).

This test verifies the end-to-end execution of:
1. Loading pre-split training data (from T019).
2. Training the Random Forest model (T024).
3. Generating the stratified baseline (T025).
4. Performing the permutation test (T026).
5. Calculating metrics and generating reports (T027-T029).

Prerequisites:
- T019 must have completed, producing `data/processed/train_set.parquet` and `data/processed/test_ood_set.parquet`.
- T024-T029 implementation must be present in `code/training.py` and `code/evaluation.py`.
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code import utils
from code import training
from code import evaluation
from code import preprocessing

# Configure logging for the test run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for paths (relative to project root)
TRAIN_SET_PATH = PROJECT_ROOT / "data" / "processed" / "train_set.parquet"
TEST_SET_PATH = PROJECT_ROOT / "data" / "processed" / "test_ood_set.parquet"
MODEL_ARTIFACT_PATH = PROJECT_ROOT / "results" / "artifacts" / "model.pkl"
TRAINING_REPORT_PATH = PROJECT_ROOT / "results" / "metrics" / "training_report.json"
PERMUTATION_REPORT_PATH = PROJECT_ROOT / "results" / "metrics" / "permutation_test_report.json"
CONFUSION_MATRIX_PATH = PROJECT_ROOT / "results" / "plots" / "confusion_matrix.png"
NULL_DISTRIBUTION_PATH = PROJECT_ROOT / "results" / "plots" / "null_distribution.png"

@pytest.fixture(scope="module")
def setup_test_environment():
    """
    Ensures required directories exist.
    Note: This test assumes T019 has already produced the data files.
    If they are missing, the test will fail early, which is the correct behavior.
    """
    dirs = [
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "results" / "artifacts",
        PROJECT_ROOT / "results" / "metrics",
        PROJECT_ROOT / "results" / "plots"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Verify prerequisites
    if not TRAIN_SET_PATH.exists():
        raise FileNotFoundError(
            f"Prerequisite data file missing: {TRAIN_SET_PATH}. "
            "Ensure T019 (OOD Split) has been completed successfully."
        )
    if not TEST_SET_PATH.exists():
        raise FileNotFoundError(
            f"Prerequisite data file missing: {TEST_SET_PATH}. "
            "Ensure T019 (OOD Split) has been completed successfully."
        )

    yield

    # Optional: Cleanup generated artifacts after test if desired
    # shutil.rmtree(PROJECT_ROOT / "results" / "artifacts", ignore_errors=True)
    # shutil.rmtree(PROJECT_ROOT / "results" / "metrics", ignore_errors=True)
    # shutil.rmtree(PROJECT_ROOT / "results" / "plots", ignore_errors=True)

def test_training_and_evaluation_pipeline(setup_test_environment):
    """
    Integration test: Runs the full training and evaluation pipeline.
    
    Steps:
    1. Load training data.
    2. Train the model (T024).
    3. Run evaluation pipeline including baseline, permutation test, and reports (T025-T029).
    4. Assert that all required artifacts are generated and valid.
    """
    logger.info("Starting Integration Test for Training and Evaluation Pipeline (T023)")

    # --- Step 1: Load Data ---
    logger.info(f"Loading training data from {TRAIN_SET_PATH}")
    try:
        # The training module expects to load data directly or via its internal logic.
        # We call the main entry point which handles loading, training, and saving.
        # However, to strictly test the pipeline flow, we might call specific functions.
        # Given the API surface, `run_training_pipeline` and `run_evaluation_pipeline` are the entry points.
        
        # Run Training (T024, T029)
        # Note: The main function in training.py likely orchestrates this.
        # We will call the specific functions to ensure they work, then verify artifacts.
        
        # Load data manually to verify format
        train_df = pd.read_parquet(TRAIN_SET_PATH)
        assert not train_df.empty, "Training data is empty."
        logger.info(f"Loaded {len(train_df)} training records.")

    except Exception as e:
        pytest.fail(f"Failed to load training data: {e}")

    # --- Step 2: Train Model ---
    logger.info("Executing Training Pipeline (T024)")
    try:
        # We call the main training logic. 
        # Based on API, `run_training_pipeline` is the orchestrator.
        # If `main` is a CLI wrapper, we might need to call `run_training_pipeline` directly.
        # Assuming `run_training_pipeline` returns the model and metrics or saves them.
        
        # Since the task T024 says "Implement training.py to train...", 
        # we assume the function `train_model` or `run_training_pipeline` exists.
        # Let's assume `run_training_pipeline` handles loading from the expected path.
        
        # To be safe and test the specific T024 logic:
        # We will call `training.main()` which is the standard entry point for these scripts.
        # But since we are in a test, we should avoid CLI side effects if possible.
        # However, the task requires the script to run.
        
        # Let's invoke the pipeline function directly if available.
        # If not, we invoke main with mocked args.
        
        # Attempt to call the pipeline function directly
        if hasattr(training, 'run_training_pipeline'):
            model, metrics = training.run_training_pipeline()
        else:
            # Fallback to main if pipeline function is not exposed, 
            # but this is less ideal for unit/integration testing.
            # We will assume the API surface provided is accurate.
            pytest.fail("training.run_training_pipeline not found in API surface.")
        
        assert model is not None, "Model was not trained."
        assert isinstance(metrics, dict), "Metrics should be a dictionary."
        logger.info("Training completed successfully.")

    except Exception as e:
        pytest.fail(f"Training pipeline failed: {e}")

    # --- Step 3: Run Evaluation ---
    logger.info("Executing Evaluation Pipeline (T025-T029)")
    try:
        if hasattr(evaluation, 'run_evaluation_pipeline'):
            eval_results = evaluation.run_evaluation_pipeline()
        else:
            pytest.fail("evaluation.run_evaluation_pipeline not found in API surface.")
        
        assert eval_results is not None, "Evaluation results are missing."
        logger.info("Evaluation completed successfully.")

    except Exception as e:
        pytest.fail(f"Evaluation pipeline failed: {e}")

    # --- Step 4: Verify Artifacts ---
    logger.info("Verifying generated artifacts...")

    # T029: Model Artifact
    assert MODEL_ARTIFACT_PATH.exists(), f"Model artifact missing: {MODEL_ARTIFACT_PATH}"
    logger.info(f"✓ Model artifact exists: {MODEL_ARTIFACT_PATH}")

    # T029: Training Report
    assert TRAINING_REPORT_PATH.exists(), f"Training report missing: {TRAINING_REPORT_PATH}"
    with open(TRAINING_REPORT_PATH, 'r') as f:
        train_report = json.load(f)
    assert 'macro_f1' in train_report, "Training report missing 'macro_f1'."
    assert 'baseline_macro_f1' in train_report, "Training report missing 'baseline_macro_f1'."
    logger.info(f"✓ Training report exists and contains metrics: {train_report['macro_f1']}")

    # T026b: Permutation Test Report
    assert PERMUTATION_REPORT_PATH.exists(), f"Permutation test report missing: {PERMUTATION_REPORT_PATH}"
    with open(PERMUTATION_REPORT_PATH, 'r') as f:
        perm_report = json.load(f)
    assert 'p_value' in perm_report, "Permutation report missing 'p_value'."
    assert 'permutation_test_passed' in perm_report, "Permutation report missing 'permutation_test_passed'."
    assert perm_report['permutation_test_passed'] is True, "Permutation test did not pass (p >= 0.05)."
    logger.info(f"✓ Permutation test report exists (p-value: {perm_report['p_value']})")

    # T028: Confusion Matrix Plot
    # Note: The path in tasks.md is results/plots/confusion_matrix.png
    # We check if the file exists.
    assert CONFUSION_MATRIX_PATH.exists(), f"Confusion matrix plot missing: {CONFUSION_MATRIX_PATH}"
    logger.info(f"✓ Confusion matrix plot exists: {CONFUSION_MATRIX_PATH}")

    # T026b: Null Distribution Plot
    assert NULL_DISTRIBUTION_PATH.exists(), f"Null distribution plot missing: {NULL_DISTRIBUTION_PATH}"
    logger.info(f"✓ Null distribution plot exists: {NULL_DISTRIBUTION_PATH}")

    logger.info("All integration tests passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])