import pytest
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
from pathlib import Path
import tempfile
import json

from src.model import evaluate_model
from src.config import ARTIFACTS_PATH

@pytest.fixture
def sample_test_data():
    """Generate deterministic sample test data."""
    np.random.seed(42)
    n_samples = 50
    X = pd.DataFrame({
        'feat1': np.random.randn(n_samples),
        'feat2': np.random.randn(n_samples),
        'feat3': np.random.randn(n_samples)
    })
    # y = 2*feat1 + 0.5*feat2 + noise
    y = 2 * X['feat1'] + 0.5 * X['feat2'] + np.random.normal(0, 0.1, n_samples)
    return X, y

@pytest.fixture
def trained_mock_model():
    """Return a pre-trained ElasticNet model."""
    model = ElasticNet(alpha=0.1, random_state=42, max_iter=1000)
    # Fit on dummy data to ensure it's trained
    X_dummy = pd.DataFrame({'a': [1, 2], 'b': [1, 2]})
    y_dummy = pd.Series([1.5, 2.5])
    model.fit(X_dummy, y_dummy)
    return model

def test_evaluate_model_returns_dict(sample_test_data, trained_mock_model):
    X_test, y_test = sample_test_data
    result = evaluate_model(trained_mock_model, X_test, y_test)
    
    assert isinstance(result, dict)
    assert 'r2' in result
    assert 'rmse' in result
    assert 'primary_method' in result

def test_evaluate_model_metrics_values(sample_test_data, trained_mock_model):
    X_test, y_test = sample_test_data
    result = evaluate_model(trained_mock_model, X_test, y_test)
    
    # R2 should be between -inf and 1.0 (usually)
    assert isinstance(result['r2'], float)
    # RMSE should be non-negative
    assert result['rmse'] >= 0.0
    assert result['primary_method'] == 'elastic_net_debiased_lasso'

def test_evaluate_model_empty_input_raises():
    model = ElasticNet()
    with pytest.raises(ValueError, match="Test sets cannot be empty"):
        evaluate_model(model, pd.DataFrame(), pd.Series())

def test_evaluate_model_invalid_types_raises():
    model = ElasticNet()
    with pytest.raises(ValueError):
        evaluate_model(model, "not_a_df", pd.Series([1, 2]))

def test_evaluate_model_saves_metrics(tmp_path, trained_mock_model, sample_test_data):
    """Test that the function can be part of a flow that saves metrics."""
    # Note: The function itself returns the dict. The saving logic is 
    # typically in run_pipeline or a wrapper, but we verify the structure here.
    X_test, y_test = sample_test_data
    metrics = evaluate_model(trained_mock_model, X_test, y_test)
    
    # Simulate saving to a temp location to ensure JSON serializability
    save_path = tmp_path / "test_metrics.json"
    with open(save_path, 'w') as f:
        json.dump(metrics, f)
    
    assert save_path.exists()
    with open(save_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == metrics