"""
Unit tests for the explainability module.
"""
import os
import json
import tempfile
import pickle
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Import the module under test
from explainability import (
    load_model,
    load_training_features,
    compute_shap_values,
    rank_features,
    run_explainability_pipeline
)

@pytest.fixture
def mock_model_artifact():
    """Create a mock model artifact."""
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    # Fit on dummy data to make it valid
    X_dummy = np.random.rand(10, 5)
    y_dummy = np.random.randint(0, 2, 10)
    model.fit(X_dummy, y_dummy)
    return {'model': model, 'metrics': {'accuracy': 0.9}}

@pytest.fixture
def mock_train_data():
    """Create a mock training dataframe."""
    df = pd.DataFrame({
        'Fe': np.random.rand(20),
        'Cr': np.random.rand(20),
        'Ni': np.random.rand(20),
        'degradation_label': np.random.randint(0, 2, 20)
    })
    return df

def test_load_model_success(mock_model_artifact, tmp_path):
    """Test successful model loading."""
    model_path = tmp_path / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(mock_model_artifact, f)
    
    result = load_model(str(model_path))
    assert 'model' in result
    assert isinstance(result['model'], RandomForestClassifier)

def test_load_model_not_found():
    """Test loading non-existent model raises error."""
    with pytest.raises(FileNotFoundError):
        load_model("non_existent_path.pkl")

def test_load_training_features(mock_train_data, tmp_path):
    """Test loading and filtering training features."""
    data_path = tmp_path / "train.parquet"
    mock_train_data.to_parquet(data_path)
    
    # Mock the load function to return our fixture directly
    # (Since we can't easily patch pd.read_parquet in this simple test without side effects)
    # Instead, we test the logic by creating a mock that returns the dataframe
    with patch('explainability.pd.read_parquet', return_value=mock_train_data):
        result = load_training_features(str(data_path))
    
    # Should exclude 'degradation_label'
    assert 'degradation_label' not in result.columns
    assert 'Fe' in result.columns
    assert 'Cr' in result.columns
    assert 'Ni' in result.columns

def test_compute_shap_values(mock_model_artifact, mock_train_data):
    """Test SHAP value computation."""
    model = mock_model_artifact['model']
    # Ensure model is fitted on compatible data
    X_dummy = mock_train_data[['Fe', 'Cr', 'Ni']].values
    y_dummy = np.random.randint(0, 2, len(X_dummy))
    model.fit(X_dummy, y_dummy)
    
    with patch('explainability.pd.read_parquet', return_value=mock_train_data):
        X = load_training_features("dummy")
    
    # Mock shap.TreeExplainer to avoid heavy computation
    with patch('explainability.shap.TreeExplainer') as MockExplainer:
        mock_explainer_instance = MagicMock()
        # Return dummy SHAP values (n_samples, n_features)
        mock_shap_vals = np.random.rand(len(X), 3)
        mock_explainer_instance.shap_values.return_value = mock_shap_vals
        mock_explainer_instance.expected_value = 0.5
        MockExplainer.return_value = mock_explainer_instance
        
        result = compute_shap_values(model, X, max_samples=5)
        
        assert 'shap_values' in result
        assert 'feature_names' in result
        assert result['n_samples_used'] == 5
        assert len(result['feature_names']) == 3

def test_rank_features():
    """Test feature ranking logic."""
    shap_data = {
        "shap_values": {
            "overall": [
                [0.1, 0.2, 0.05], # sample 1
                [0.15, 0.1, 0.08] # sample 2
            ]
        },
        "feature_names": ["Fe", "Cr", "Ni"]
    }
    
    ranked = rank_features(shap_data)
    
    assert len(ranked) == 3
    # Cr should be first (mean abs: (0.2+0.1)/2 = 0.15)
    # Fe should be second (mean abs: (0.1+0.15)/2 = 0.125)
    # Ni should be last
    assert ranked[0]['feature'] == 'Cr'
    assert ranked[0]['mean_abs_shap'] == 0.15
    assert ranked[1]['feature'] == 'Fe'
    assert ranked[2]['feature'] == 'Ni'

@patch('explainability.load_model')
@patch('explainability.load_training_features')
@patch('explainability.compute_shap_values')
@patch('explainability.rank_features')
@patch('explainability.generate_shap_plot')
@patch('explainability.save_json')
def test_run_explainability_pipeline(
    mock_save_json,
    mock_gen_plot,
    mock_rank,
    mock_shap,
    mock_load_feat,
    mock_load_model,
    tmp_path
):
    """Test the full pipeline execution."""
    # Setup mocks
    mock_load_model.return_value = {'model': RandomForestClassifier()}
    mock_load_feat.return_value = pd.DataFrame({'Fe': [1], 'Cr': [1]})
    mock_shap.return_value = {
        'shap_values': {'overall': [[0.1, 0.2]]},
        'feature_names': ['Fe', 'Cr'],
        'n_samples_used': 1
    }
    mock_rank.return_value = [{'feature': 'Cr', 'mean_abs_shap': 0.2}]
    
    # Change working directory to tmp to avoid writing to real paths during test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        result = run_explainability_pipeline()
        
        assert result is not None
        mock_load_model.assert_called_once()
        mock_load_feat.assert_called_once()
        mock_shap.assert_called_once()
        mock_rank.assert_called_once()
        mock_gen_plot.assert_called_once()
        mock_save_json.assert_called_once()
    finally:
        os.chdir(original_cwd)