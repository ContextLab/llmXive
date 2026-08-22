"""
Integration test for T018: Verifying RF and XGBoost train within 30 mins on 2-core CPU without GPU errors.

This test validates:
1. Data loading and splitting (US1 output)
2. Model training (RF and XGBoost) completes successfully
3. Training time is within the 30-minute limit (1800 seconds)
4. No GPU-related errors occur (CPU-only execution)
5. Models are saved and can be loaded
"""

import os
import sys
import time
import pytest
import joblib
import tempfile
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config, ensure_directories
from data.split import perform_stratified_split, save_split_metadata
from models.train import train_random_forest, train_xgboost, save_models
from utils.logging import DataPipelineLog


@pytest.mark.integration
def test_rf_xgboost_training_time_and_success():
    """
    Integration test verifying RF and XGBoost train within 30 mins on 2-core CPU without GPU errors.
    
    This test:
    1. Loads the preprocessed dataset from data/processed/merged_dataset.csv
    2. Performs stratified split (or uses existing split if available)
    3. Trains RandomForest and XGBoost models with n_jobs=2 (CPU-only)
    4. Measures training time and ensures it's under 1800 seconds (30 mins)
    5. Verifies models are saved and can be loaded
    6. Ensures no GPU errors occur (XGBoost configured for CPU)
    """
    
    # Setup
    config = get_config()
    ensure_directories()
    logger = DataPipelineLog("integration_test_train")
    
    # Constants
    MAX_TRAINING_TIME_SECONDS = 1800  # 30 minutes
    N_ESTIMULATORS = 100  # Use smallest grid value for speed in integration test
    N_JOBS = 2  # Enforce 2-core CPU usage
    
    # Paths
    merged_data_path = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
    models_dir = PROJECT_ROOT / "data" / "models"
    
    # Verify input data exists
    assert merged_data_path.exists(), f"Merged dataset not found at {merged_data_path}. Run US1 first."
    
    # Load and prepare data
    logger.info("Loading merged dataset for training integration test")
    import pandas as pd
    df = pd.read_csv(merged_data_path)
    
    # Identify feature columns (exclude 'label' and 'species_id')
    feature_cols = [col for col in df.columns if col not in ['label', 'species_id']]
    target_col = 'label'
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Perform stratified split
    logger.info("Performing stratified train-test split")
    X_train, X_test, y_train, y_test, split_metadata = perform_stratified_split(
        X, y, test_size=0.2, random_state=config['random_seed']
    )
    
    # Save split metadata
    split_metadata_path = PROJECT_ROOT / "data" / "processed" / "split_metadata.json"
    save_split_metadata(split_metadata, str(split_metadata_path))
    
    # Create temporary directory for model saving during test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test RandomForest Training
        logger.info(f"Starting RandomForest training (n_estimators={N_ESTIMULATORS}, n_jobs={N_JOBS})")
        start_time = time.time()
        
        rf_model, rf_metrics = train_random_forest(
            X_train, y_train, 
            n_estimators=N_ESTIMULATORS, 
            n_jobs=N_JOBS,
            random_state=config['random_seed']
        )
        
        rf_training_time = time.time() - start_time
        logger.info(f"RandomForest training completed in {rf_training_time:.2f} seconds")
        
        # Verify training time
        assert rf_training_time < MAX_TRAINING_TIME_SECONDS, \
            f"RandomForest training took {rf_training_time:.2f}s, exceeding limit of {MAX_TRAINING_TIME_SECONDS}s"
        
        # Save and verify RF model
        rf_model_path = os.path.join(temp_dir, "random_forest.joblib")
        save_models({"random_forest": rf_model}, temp_dir)
        assert os.path.exists(rf_model_path), "RandomForest model not saved"
        
        # Load and verify RF model
        loaded_rf = joblib.load(rf_model_path)
        assert loaded_rf is not None, "Failed to load RandomForest model"
        
        # Test XGBoost Training
        logger.info(f"Starting XGBoost training (n_estimators={N_ESTIMULATORS}, n_jobs={N_JOBS})")
        start_time = time.time()
        
        xgb_model, xgb_metrics = train_xgboost(
            X_train, y_train,
            n_estimators=N_ESTIMULATORS,
            n_jobs=N_JOBS,
            random_state=config['random_seed']
        )
        
        xgb_training_time = time.time() - start_time
        logger.info(f"XGBoost training completed in {xgb_training_time:.2f} seconds")
        
        # Verify training time
        assert xgb_training_time < MAX_TRAINING_TIME_SECONDS, \
            f"XGBoost training took {xgb_training_time:.2f}s, exceeding limit of {MAX_TRAINING_TIME_SECONDS}s"
        
        # Save and verify XGBoost model
        xgb_model_path = os.path.join(temp_dir, "xgboost.joblib")
        save_models({"xgboost": xgb_model}, temp_dir)
        assert os.path.exists(xgb_model_path), "XGBoost model not saved"
        
        # Load and verify XGBoost model
        loaded_xgb = joblib.load(xgb_model_path)
        assert loaded_xgb is not None, "Failed to load XGBoost model"
        
        # Verify no GPU errors (XGBoost should use CPU when n_jobs is set and GPU not configured)
        # This is implicitly verified by successful execution without GPU-related exceptions
        
        # Log results
        logger.info(f"Integration test passed: RF={rf_training_time:.2f}s, XGB={xgb_training_time:.2f}s")
        logger.info(f"Both models trained successfully within {MAX_TRAINING_TIME_SECONDS}s limit")
        
        # Assert total time is within limit
        total_time = rf_training_time + xgb_training_time
        assert total_time < MAX_TRAINING_TIME_SECONDS, \
            f"Total training time ({total_time:.2f}s) exceeded {MAX_TRAINING_TIME_SECONDS}s"
        
        # Verify metrics were generated
        assert rf_metrics is not None, "RandomForest metrics are None"
        assert xgb_metrics is not None, "XGBoost metrics are None"
        assert 'roc_auc' in rf_metrics or 'accuracy' in rf_metrics, "RF metrics missing key fields"
        assert 'roc_auc' in xgb_metrics or 'accuracy' in xgb_metrics, "XGB metrics missing key fields"
    
    logger.info("T018 Integration Test: PASSED")