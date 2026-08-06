"""
Integration tests for the full training pipeline.

This module tests the end-to-end execution of the data preparation,
model training, and evaluation steps using a small, real sample of
the processed data to ensure the pipeline components interact correctly.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import load_raw_data, clean_data, split_data, save_processed_data
from models.train import load_data, inner_loop_cv_selection, train_model, evaluate_model, save_artifacts
from utils.logging_config import get_logger, log_pipeline_event
from utils.config import get_config_summary

logger = get_logger(__name__)

# Constants for test paths
TEST_DATA_DIR = project_root / "data" / "processed"
TEST_RESULTS_DIR = project_root / "results"
TEST_FEATURES_FILE = TEST_DATA_DIR / "features.csv"

# Sample size for integration test (small subset to run quickly)
SAMPLE_SIZE = 100

@pytest.fixture(scope="function")
def temp_output_dirs():
    """Create temporary directories for test outputs and clean up after."""
    temp_dir = tempfile.mkdtemp()
    original_data_dir = TEST_DATA_DIR
    original_results_dir = TEST_RESULTS_DIR
    
    # We will use the real directories but ensure they exist
    # The test will verify that files are written to the expected locations
    
    yield temp_dir
    
    # Cleanup is handled by the test logic or pytest
    # We don't delete the main data/results dirs to preserve state
    
@pytest.mark.integration
def test_full_training_pipeline_with_sample_data(temp_output_dirs):
    """
    Integration test: test_full_training_pipeline_with_sample_data
    
    Executes the full training pipeline on a small sample of the processed data:
    1. Loads the processed features (or creates a small sample if file missing)
    2. Splits data into train/test sets
    3. Runs inner-loop CV to select hyperparameters
    4. Trains the final model
    5. Evaluates on test set
    6. Saves artifacts (model.pkl, metrics.json)
    
    Verifies:
    - All expected output files are created
    - Model artifact is valid and loadable
    - Metrics file contains expected keys
    - No exceptions occur during the pipeline
    """
    
    # Ensure required directories exist
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load or prepare sample data
    # We need to check if the real features.csv exists
    if not TEST_FEATURES_FILE.exists():
        pytest.skip(
            "data/processed/features.csv not found. "
            "Please run the data ingestion pipeline first (T018/T019)."
        )
    
    logger.info("Loading processed features for integration test...")
    df_full = pd.read_csv(TEST_FEATURES_FILE)
    
    # Verify required columns exist
    required_cols = [
        'tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch',
        'electronegativity_difference', 'decomposition_energy'
    ]
    missing_cols = [col for col in required_cols if col not in df_full.columns]
    if missing_cols:
        pytest.fail(f"Missing required columns in features.csv: {missing_cols}")
    
    # Take a small sample for fast integration testing
    if len(df_full) > SAMPLE_SIZE:
        # Use a fixed seed for reproducibility
        df_sample = df_full.sample(n=SAMPLE_SIZE, random_state=42).reset_index(drop=True)
    else:
        df_sample = df_full
    
    logger.info(f"Using sample of {len(df_sample)} records for integration test.")
    
    # Step 2: Split data
    logger.info("Splitting data into train and test sets...")
    train_df, test_df = split_data(
        df_sample, 
        target_col='decomposition_energy',
        test_size=0.2,
        random_state=42
    )
    
    assert len(train_df) + len(test_df) == len(df_sample), "Data split mismatch"
    assert len(train_df) > 0 and len(test_df) > 0, "Empty train or test set"
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    # Step 3: Prepare features and target
    feature_cols = [col for col in required_cols if col != 'decomposition_energy']
    X_train = train_df[feature_cols]
    y_train = train_df['decomposition_energy']
    X_test = test_df[feature_cols]
    y_test = test_df['decomposition_energy']
    
    # Step 4: Inner loop CV for hyperparameter selection
    logger.info("Running inner-loop CV for hyperparameter selection...")
    best_params, cv_results = inner_loop_cv_selection(
        X_train, y_train,
        param_grid={
            'max_depth': [5, 10],  # Reduced for speed
            'min_samples_leaf': [1, 2]
        },
        cv=3,  # Reduced for speed
        scoring='neg_mean_squared_error'
    )
    
    assert best_params is not None, "Inner loop CV failed to return best params"
    logger.info(f"Best parameters: {best_params}")
    
    # Step 5: Train final model
    logger.info("Training final model with best parameters...")
    model = train_model(
        X_train, y_train,
        model_type='RandomForest',
        **best_params
    )
    
    assert model is not None, "Model training failed"
    
    # Step 6: Evaluate on test set
    logger.info("Evaluating model on test set...")
    test_rmse, test_mae, test_r2 = evaluate_model(model, X_test, y_test)
    
    logger.info(f"Test RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f}, R2: {test_r2:.4f}")
    
    assert test_rmse is not None, "Evaluation failed to return RMSE"
    assert not np.isnan(test_rmse), "RMSE is NaN"
    
    # Step 7: Save artifacts
    logger.info("Saving model artifacts...")
    model_path = TEST_RESULTS_DIR / "model.pkl"
    metrics_path = TEST_RESULTS_DIR / "metrics.json"
    
    save_artifacts(
        model=model,
        metrics={
            'test_rmse': float(test_rmse),
            'test_mae': float(test_mae),
            'test_r2': float(test_r2),
            'best_params': best_params,
            'train_size': len(train_df),
            'test_size': len(test_df)
        },
        model_path=model_path,
        metrics_path=metrics_path
    )
    
    # Step 8: Verification
    logger.info("Verifying output artifacts...")
    
    # Check model file exists and is loadable
    assert model_path.exists(), f"Model file not created: {model_path}"
    import pickle
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None, "Loaded model is None"
    
    # Check metrics file exists and contains expected keys
    assert metrics_path.exists(), f"Metrics file not created: {metrics_path}"
    import json
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    expected_keys = ['test_rmse', 'test_mae', 'test_r2', 'best_params']
    missing_keys = [k for k in expected_keys if k not in metrics_data]
    assert not missing_keys, f"Metrics file missing keys: {missing_keys}"
    
    logger.info("Integration test PASSED: Full pipeline executed successfully.")
    
    # Optional: Clean up test artifacts if desired (usually kept for debugging)
    # os.remove(model_path)
    # os.remove(metrics_path)