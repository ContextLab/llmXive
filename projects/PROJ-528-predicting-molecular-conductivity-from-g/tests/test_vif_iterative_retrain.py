"""
Unit tests for the iterative VIF retraining logic (T039).
"""
import pytest
import numpy as np
import pandas as pd
import os
import json
import tempfile
import shutil

from code.vif_iterative_retrain import (
    prepare_features_and_target,
    iterative_vif_retrain,
    train_model,
    evaluate_model
)
from code.config import SEED, VIF_THRESHOLD

# Mock data for testing
@pytest.fixture
def mock_data():
    """Create a mock DataFrame with high VIF features."""
    np.random.seed(SEED)
    n_samples = 100
    # Create highly correlated features
    base = np.random.randn(n_samples)
    f1 = base + np.random.normal(0, 0.1, n_samples)
    f2 = base * 2 + np.random.normal(0, 0.1, n_samples)  # Highly correlated with f1
    f3 = np.random.randn(n_samples)  # Independent
    f4 = np.random.randn(n_samples)  # Independent
    target = f1 + f3 + np.random.normal(0, 0.5, n_samples)

    smiles = [f"SMILES_{i}" for i in range(n_samples)]
    status = ["valid"] * n_samples

    df = pd.DataFrame({
        "smiles": smiles,
        "status": status,
        "f1": f1,
        "f2": f2,
        "f3": f3,
        "f4": f4,
        "conductivity": target
    })
    return df

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_prepare_features_and_target(mock_data):
    """Test feature and target preparation."""
    X, y, feature_names = prepare_features_and_target(mock_data, 'conductivity')
    assert X.shape[0] == mock_data.shape[0]
    assert len(feature_names) == 4  # f1, f2, f3, f4
    assert 'f1' in feature_names
    assert 'f2' in feature_names
    assert len(y) == mock_data.shape[0]

def test_train_model_rf():
    """Test Random Forest model training."""
    np.random.seed(SEED)
    X = np.random.randn(50, 5)
    y = np.random.randn(50)
    model = train_model(X, y, model_type='rf')
    assert model is not None
    assert hasattr(model, 'predict')

def test_train_model_gb():
    """Test Gradient Boosting model training."""
    np.random.seed(SEED)
    X = np.random.randn(50, 5)
    y = np.random.randn(50)
    model = train_model(X, y, model_type='gb')
    assert model is not None
    assert hasattr(model, 'predict')

def test_evaluate_model():
    """Test model evaluation."""
    np.random.seed(SEED)
    X_train = np.random.randn(50, 5)
    y_train = np.random.randn(50)
    X_test = np.random.randn(20, 5)
    y_test = np.random.randn(20)

    model = train_model(X_train, y_train, model_type='rf')
    metrics = evaluate_model(model, X_test, y_test)

    assert 'r2' in metrics
    assert 'mae' in metrics
    assert isinstance(metrics['r2'], float)
    assert isinstance(metrics['mae'], float)

def test_iterative_vif_retrain(mock_data, temp_dir):
    """Test the full iterative VIF retraining loop."""
    # Save mock data to temp file
    data_path = os.path.join(temp_dir, "test_descriptors.csv")
    mock_data.to_csv(data_path, index=False)

    output_path = os.path.join(temp_dir, "test_vif_log.json")

    # Run the iterative retraining
    result = iterative_vif_retrain(
        data_path=data_path,
        target_col="conductivity",
        model_type="rf",
        output_path=output_path,
        vif_threshold=VIF_THRESHOLD
    )

    # Verify output file exists
    assert os.path.exists(output_path)

    # Verify result structure
    assert 'threshold' in result
    assert 'log' in result
    assert 'final_features' in result
    assert 'final_metrics' in result

    # Verify that at least one feature was removed (since f1 and f2 are highly correlated)
    # We expect f2 to be removed first due to high VIF
    assert len(result['removed_features']) > 0
    assert len(result['final_features']) < 4  # Should have removed at least one

    # Verify final VIF scores are all below threshold
    if result['final_vif_scores']:
        assert all(v <= VIF_THRESHOLD for v in result['final_vif_scores'])

    # Verify log entries
    for entry in result['log']:
        assert 'iteration' in entry
        assert 'removed_feature' in entry
        assert 'remaining_features' in entry
        assert 'metrics' in entry
        assert 'r2' in entry['metrics']
        assert 'mae' in entry['metrics']