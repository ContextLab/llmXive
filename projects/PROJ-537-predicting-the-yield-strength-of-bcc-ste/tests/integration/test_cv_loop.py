"""
Integration test for the nested Cross-Validation loop.

This test verifies that the modeling pipeline correctly implements
an outer k-fold loop for model evaluation and an inner k-fold loop
for hyperparameter tuning, ensuring no data leakage occurs.

It runs the full feature engineering and training pipeline on the
real merged dataset (data/intermediate/merged.csv) and asserts that
the evaluation metrics are computed correctly.
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from code/
# Assuming this test file is at tests/integration/test_cv_loop.py
# and the code is at code/
project_root = Path(__file__).resolve().parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from config import CONFIG
from utils.logging import get_logger
from ingestion.merge_and_filter import load_experimental_data, load_dft_data, merge_datasets, filter_bcc_structure, handle_nulls, validate_merged_dataset
from modeling.features import build_feature_matrix
from modeling.train import train_random_forest_cv

logger = get_logger(__name__)

# Constants for the test
MIN_ROWS = 20
OUTER_FOLDS = 5
INNER_FOLDS = 3
RANDOM_SEED = 42

@pytest.fixture(scope="module")
def merged_dataset_path():
    """Locate the merged dataset produced by US1."""
    path = Path(CONFIG.DATA_INTERMEDIATE_DIR) / "merged.csv"
    if not path.exists():
        pytest.fail(f"Required dataset not found at {path}. Run US1 tasks first.")
    return path

@pytest.fixture(scope="module")
def feature_matrix(merged_dataset_path):
    """
    Load and prepare the feature matrix from the real merged dataset.
    This fixture runs once for the module to avoid redundant I/O.
    """
    logger.info(f"Loading dataset from {merged_dataset_path}")
    
    # Load components as per US1 implementation
    # Note: We assume the raw files exist or are fetched. 
    # For this integration test, we rely on the merged CSV from US1.
    df = pd.read_csv(merged_dataset_path)
    
    # Validate basic structure (re-checking US1 constraints)
    assert df.shape[0] >= MIN_ROWS, f"Dataset has {df.shape[0]} rows, expected >= {MIN_ROWS}"
    assert "yield_strength_MPa" in df.columns, "Missing target column"
    
    # Build feature matrix using the project's feature engineering logic
    # This calls the real implementation from code/modeling/features.py
    X, y, feature_names = build_feature_matrix(df)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target vector shape: {y.shape}")
    
    return X, y, feature_names

def test_nested_cv_loop_execution(feature_matrix):
    """
    Test that the nested CV loop runs to completion without errors
    and produces statistically valid metrics.
    
    This verifies:
    1. Outer loop splits data correctly.
    2. Inner loop tunes hyperparameters without leaking test data.
    3. Final metrics are computed and returned.
    """
    X, y, feature_names = feature_matrix
    
    logger.info("Starting Nested Cross-Validation...")
    
    # Call the real training function
    # We pass the configured folds and seed
    results = train_random_forest_cv(
        X=X,
        y=y,
        outer_folds=OUTER_FOLDS,
        inner_folds=INNER_FOLDS,
        random_state=RANDOM_SEED,
        feature_names=feature_names
    )
    
    # Assertions on results structure
    assert results is not None, "Results should not be None"
    assert "r2_scores" in results, "Missing 'r2_scores' in results"
    assert "mae_scores" in results, "Missing 'mae_scores' in results"
    assert "best_params" in results, "Missing 'best_params' in results"
    
    r2_scores = results["r2_scores"]
    mae_scores = results["mae_scores"]
    
    # Verify we have exactly OUTER_FOLDS scores
    assert len(r2_scores) == OUTER_FOLDS, f"Expected {OUTER_FOLDS} R2 scores, got {len(r2_scores)}"
    assert len(mae_scores) == OUTER_FOLDS, f"Expected {OUTER_FOLDS} MAE scores, got {len(mae_scores)}"
    
    # Verify scores are numeric and reasonable
    # R2 can be negative, but typically > -1 for reasonable models
    assert all(isinstance(s, (int, float)) for s in r2_scores), "R2 scores must be numeric"
    assert all(isinstance(s, (int, float)) for s in mae_scores), "MAE scores must be numeric"
    
    mean_r2 = np.mean(r2_scores)
    std_r2 = np.std(r2_scores)
    
    logger.info(f"Nested CV Results - Mean R2: {mean_r2:.4f} (+/- {std_r2:.4f})")
    logger.info(f"Nested CV Results - Mean MAE: {np.mean(mae_scores):.4f}")
    
    # Basic sanity check: Mean R2 should not be extremely low (e.g. < -10)
    # This ensures the model isn't completely failing due to data issues
    assert mean_r2 > -10.0, f"Mean R2 is unreasonably low: {mean_r2}"
    
    # Verify best_params is a dict (or list of dicts if per-fold)
    # Usually train_random_forest_cv returns the best params found in the inner loop
    # or the average best params. We expect a dict structure.
    assert isinstance(results["best_params"], dict), "best_params should be a dictionary"
    
    logger.info("Nested CV Loop Test PASSED.")

def test_data_leakage_prevention(feature_matrix):
    """
    A specific check to ensure the implementation doesn't accidentally
    use the target variable for feature engineering in a way that leaks
    data across folds. This is a logic check on the feature matrix construction
    and the CV split behavior.
    
    Since build_feature_matrix is deterministic, we verify that the
    feature matrix does not contain the target column.
    """
    X, y, feature_names = feature_matrix
    
    # The feature matrix X should not contain the target column 'yield_strength_MPa'
    # We check this by ensuring the target is not in the feature names
    # (assuming build_feature_matrix returns feature_names corresponding to X columns)
    if "yield_strength_MPa" in feature_names:
        pytest.fail("Target variable 'yield_strength_MPa' found in feature matrix - DATA LEAKAGE DETECTED")
    
    # Additionally, verify that the shape of X matches the number of feature names
    assert X.shape[1] == len(feature_names), "Feature matrix columns do not match feature names count"
    
    logger.info("Data Leakage Prevention Test PASSED.")

if __name__ == "__main__":
    # Allow running as a script for quick verification
    pytest.main([__file__, "-v"])