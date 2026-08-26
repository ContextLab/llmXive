import pytest
import os
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestRegressor
import joblib

# Import the module under test
import code.modeling as modeling
from code.modeling import (
    load_features_and_target,
    train_random_forest_with_cv,
    run_repeated_cv,
    evaluate_model_on_test,
    save_model,
    save_model_metrics,
    write_methodological_flags,
    run_modeling_pipeline
)

@pytest.fixture
def mock_data():
    """Create mock data for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'ilr_0': np.random.randn(n),
        'ilr_1': np.random.randn(n),
        'ilr_2': np.random.randn(n),
        'ilr_3': np.random.randn(n),
        'ilr_4': np.random.randn(n),
        'poisson_ratio': np.random.randn(n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_split_indices():
    """Create mock split indices."""
    return {
        'train': list(range(80)),
        'val': list(range(80, 90)),
        'test': list(range(90, 100))
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('code.modeling.get_config')
@patch('code.modeling.pd.read_parquet')
def test_load_features_and_target(mock_read, mock_config, mock_data, temp_dir):
    """Test loading features and target from parquet."""
    # Setup mocks
    mock_config.return_value.data_processed = temp_dir
    mock_read.return_value = mock_data
    
    # Mock the file existence check
    with patch('code.modeling.os.path.exists', return_value=True):
        X, y = load_features_and_target(str(temp_dir / "alloys_clean.parquet"))
    
    assert X.shape[0] == 100
    assert y.shape[0] == 100
    assert list(X.columns) == ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']

def test_rf_training_converges(mock_data):
    """Test that Random Forest training converges without error."""
    X = mock_data[['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']]
    y = mock_data['poisson_ratio']
    
    model = train_random_forest_with_cv(X, y, n_estimators=10, random_state=42)
    
    assert isinstance(model, RandomForestRegressor)
    assert model.n_estimators == 10
    # Check that model can predict
    predictions = model.predict(X)
    assert len(predictions) == len(y)

def test_cv_split_reproducibility(mock_data):
    """Test that repeated CV produces consistent results with fixed seed."""
    X = mock_data[['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']]
    y = mock_data['poisson_ratio']
    
    # Run twice with same seed
    result1 = run_repeated_cv(X, y, n_splits=3, n_repeats=2, random_state=42)
    result2 = run_repeated_cv(X, y, n_splits=3, n_repeats=2, random_state=42)
    
    assert result1['cv_mae'] == result2['cv_mae']
    assert result1['cv_ci_lower'] == result2['cv_ci_lower']
    assert result1['cv_ci_upper'] == result2['cv_ci_upper']

def test_save_model_creates_directory(temp_dir):
    """Test that save_model creates the models directory if it doesn't exist."""
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model_path = temp_dir / "models" / "rf_model.pkl"
    
    # Directory should not exist yet
    assert not model_path.parent.exists()
    
    # Save model
    result_path = save_model(model, str(model_path))
    
    # Directory should now exist
    assert model_path.parent.exists()
    assert model_path.exists()
    
    # Verify file can be loaded
    loaded_model = joblib.load(result_path)
    assert isinstance(loaded_model, RandomForestRegressor)

def test_save_model_metrics(temp_dir):
    """Test saving model metrics to JSON."""
    metrics = {
        'cv_mae': 0.05,
        'cv_ci_lower': 0.04,
        'cv_ci_upper': 0.06,
        'test_mae': 0.055
    }
    output_path = temp_dir / "model_metrics.json"
    
    save_model_metrics(metrics, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics['cv_mae'] == 0.05
    assert saved_metrics['test_mae'] == 0.055

def test_write_methodological_flags(temp_dir):
    """Test writing methodological flags."""
    output_path = temp_dir / "methodological_flags.json"
    
    # Test flag True (MAE > 0.05)
    write_methodological_flags(0.06, str(output_path))
    
    with open(output_path, 'r') as f:
        flags = json.load(f)
    
    assert flags['mae_flag'] is True
    assert flags['cv_mae'] == 0.06
    
    # Test flag False (MAE <= 0.05)
    write_methodological_flags(0.04, str(output_path))
    
    with open(output_path, 'r') as f:
        flags = json.load(f)
    
    assert flags['mae_flag'] is False

def test_evaluate_model_on_test(mock_data):
    """Test evaluation on test set."""
    X = mock_data[['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']]
    y = mock_data['poisson_ratio']
    
    model = train_random_forest_with_cv(X, y, n_estimators=10, random_state=42)
    
    # Use a subset as test
    X_test = X.iloc[:10]
    y_test = y.iloc[:10]
    
    results = evaluate_model_on_test(model, X_test, y_test)
    
    assert 'test_mae' in results
    assert 'residuals' in results
    assert len(results['residuals']) == 10
    assert results['test_mae'] >= 0