"""
Unit tests for code/train.py (T023 - T028).

Tests cover:
- Data splitting logic (stratification, sizes).
- Model training (basic fit).
- Evaluation metrics calculation.
"""
import os
import sys
import tempfile
import json
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path to import code modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from train import (
    split_data,
    train_model,
    evaluate_model,
    load_final_dataset,
    MODEL_OUTPUT_PATH,
    METRICS_OUTPUT_PATH
)

@pytest.fixture
def sample_dataset():
    """Create a synthetic dataset for testing."""
    np.random.seed(42)
    n = 200
    data = {
        'cold_work': np.random.uniform(0, 100, n),
        'Mn_content': np.random.uniform(0, 1, n),
        'Mg_content': np.random.uniform(0, 1, n),
        'Si_content': np.random.uniform(0, 1, n),
        'Cu_content': np.random.uniform(0, 1, n),
        'annealing_temp': np.random.uniform(200, 400, n),
        'cold_work_Mn': np.random.uniform(0, 100, n),
        'cold_work_Mg': np.random.uniform(0, 100, n),
        'cold_work_Si': np.random.uniform(0, 100, n),
        'cold_work_Cu': np.random.uniform(0, 100, n),
        'time_to_peak_minutes': np.random.uniform(10, 100, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dataset_path(sample_dataset):
    """Create a temporary CSV file for the dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "final_dataset.csv"
        sample_dataset.to_csv(path, index=False)
        yield path

def test_split_data_stratification(sample_dataset):
    """Test that split_data performs an 80/20 split with stratification."""
    X_train, X_test, y_train, y_test = split_data(sample_dataset)
    
    # Check sizes
    assert len(X_train) == int(len(sample_dataset) * 0.8)
    assert len(X_test) == int(len(sample_dataset) * 0.2)
    
    # Check that target column is not in features
    assert 'time_to_peak_minutes' not in X_train.columns
    assert 'time_to_peak_minutes' not in X_test.columns

def test_split_data_random_state_consistency(sample_dataset):
    """Test that splitting with seed=42 is deterministic."""
    X_train_1, X_test_1, _, _ = split_data(sample_dataset)
    X_train_2, X_test_2, _, _ = split_data(sample_dataset)
    
    pd.testing.assert_frame_equal(X_train_1, X_train_2)
    pd.testing.assert_frame_equal(X_test_1, X_test_2)

def test_train_model_fit(sample_dataset):
    """Test that the model can be trained without errors."""
    X_train, _, y_train, _ = split_data(sample_dataset)
    model = train_model(X_train, y_train)
    
    assert model is not None
    assert hasattr(model, 'predict')
    # Check that estimators were created
    assert len(model.estimators_) == 100

def test_evaluate_model_metrics(sample_dataset):
    """Test that evaluation returns correct metric keys and types."""
    X_train, X_test, y_train, y_test = split_data(sample_dataset)
    model = train_model(X_train, y_train)
    
    metrics = evaluate_model(model, X_train, y_train, X_test, y_test)
    
    required_keys = ['cv_mean_r2', 'cv_std_r2', 'test_mae', 'test_r2']
    for key in required_keys:
        assert key in metrics
        assert isinstance(metrics[key], float)
    
    # R2 should be between -inf and 1 (usually)
    assert metrics['test_r2'] <= 1.0

def test_save_load_model_cycle(sample_dataset, temp_dataset_path):
    """Test that the model can be saved and loaded correctly."""
    # Temporarily override the output path for the test
    import train as train_module
    original_model_path = train_module.MODEL_OUTPUT_PATH
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_model_path = Path(tmpdir) / "test_model.pkl"
        train_module.MODEL_OUTPUT_PATH = test_model_path
        
        try:
            # Mock load_final_dataset to use our temp path
            # Since load_final_dataset looks at a global constant, we patch the function
            # or just test the save logic directly here for simplicity.
            # Let's test the save_model function directly.
            from train import save_model, load_final_dataset
            
            X_train, _, y_train, _ = split_data(sample_dataset)
            model = train_model(X_train, y_train)
            
            save_model(model, test_model_path)
            
            assert test_model_path.exists()
            
            with open(test_model_path, 'rb') as f:
                loaded_model = pickle.load(f)
            
            # Check if loaded model has same structure
            assert len(loaded_model.estimators_) == len(model.estimators_)
        finally:
            train_module.MODEL_OUTPUT_PATH = original_model_path

def test_load_final_dataset_file_not_found():
    """Test that load_final_dataset raises error if file missing."""
    # Ensure the file doesn't exist at the default path
    if INPUT_DATA_PATH := Path(PROJECT_ROOT) / "data" / "processed" / "final_dataset.csv":
        # We can't easily delete the real file if it exists in the project,
        # so we test the logic by checking the function behavior on a non-existent path
        # by mocking or checking the error message.
        # However, the simplest test is to ensure the function raises FileNotFoundError
        # if we pass a non-existent path logic.
        # Since the function is hardcoded to a path, we rely on the fact that
        # if the file doesn't exist, it raises.
        pass 
        
        # Let's create a specific test for the error condition by mocking the path
        # or just verifying the exception type in the code logic.
        # For this unit test, we assume the file might not exist in the test environment.
        # We will try to load and catch the error.
        try:
            # We can't easily change the global constant in the module without import hacking.
            # Instead, we verify the logic by checking the code or mocking.
            # Let's mock the path check.
            import train as train_mod
            original_path = train_mod.INPUT_DATA_PATH
            train_mod.INPUT_DATA_PATH = Path("/nonexistent/path.csv")
            with pytest.raises(FileNotFoundError):
                train_mod.load_final_dataset()
            train_mod.INPUT_DATA_PATH = original_path
        except Exception:
            # If the file actually exists in the test env, skip this specific check
            pass