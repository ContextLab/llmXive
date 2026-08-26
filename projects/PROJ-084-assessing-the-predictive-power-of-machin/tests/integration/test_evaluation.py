"""
Integration tests for the model evaluation pipeline (T026).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.modeling.evaluate import main, evaluate_model, load_model_artifacts
from code.config import PROJECT_ROOT

@pytest.fixture
def mock_test_data():
    """Generate mock test data for evaluation."""
    n_samples = 100
    n_features = 2048
    X = np.random.rand(n_samples, n_features)
    y = np.random.rand(n_samples) * 100  # Yields 0-100
    return X, y

@pytest.fixture
def mock_model():
    """Return a dummy trained model."""
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    # Fit on dummy data to make it "trained"
    X_dummy = np.random.rand(10, 2048)
    y_dummy = np.random.rand(10)
    model.fit(X_dummy, y_dummy)
    return model

def test_evaluate_model_metrics(mock_test_data, mock_model):
    """Test that evaluate_model returns correct metric structure."""
    X, y = mock_test_data
    metrics = evaluate_model(mock_model, X, y, "TestRF")
    
    assert "model_name" in metrics
    assert metrics["model_name"] == "TestRF"
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "n_samples" in metrics
    assert metrics["n_samples"] == len(y)
    
    # Check types
    assert isinstance(metrics["r2"], float)
    assert isinstance(metrics["rmse"], float)
    assert isinstance(metrics["mae"], float)

@patch('code.modeling.evaluate.load_parquet')
@patch('code.modeling.evaluate.MODELS_DIR')
@patch('code.modeling.evaluate.RESULTS_DIR')
def test_main_execution_flow(mock_results_dir, mock_models_dir, mock_load_parquet, mock_test_data, mock_model):
    """Test the main function execution flow with mocked dependencies."""
    # Setup mocks
    mock_results_dir.mkdir.return_value = None
    mock_models_dir.mkdir.return_value = None
    
    # Mock split data
    split_df = pd.DataFrame({
        'index': list(range(100)),
        'split': ['test'] * 100
    })
    
    # Mock cleaned data
    # Create columns: 'yield' and 2048 fingerprint columns
    feature_cols = [f'fp_{i}' for i in range(2048)]
    cleaned_df = pd.DataFrame(
        np.random.rand(100, 2049),
        columns=['yield'] + feature_cols
    )
    
    mock_load_parquet.side_effect = [split_df, cleaned_df]
    
    # Mock model loading
    with patch('code.modeling.evaluate.load_model_artifacts') as mock_load_artifacts:
        mock_load_artifacts.return_value = (mock_model, {'n_estimators': 10})
        
        # Run main
        result = main()
        
        # Assertions
        assert "metrics" in result
        assert "random_forest" in result["metrics"]
        assert result["metrics"]["random_forest"]["status"] != "skipped"
        
        # Check that files were created (mocked)
        mock_results_dir.mkdir.assert_called()

def test_load_model_artifacts_file_not_found():
    """Test that load_model_artifacts raises FileNotFoundError if files missing."""
    with patch('code.modeling.evaluate.MODELS_DIR', Path('/nonexistent/path')):
        with pytest.raises(FileNotFoundError):
            load_model_artifacts('rf')