"""
Unit tests for the trainer module (T013).

These tests verify:
1. Data loading logic
2. Grid search execution (mocked to avoid long runtime)
3. Metric calculation
4. Artifact saving
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
from code.models import trainer


@pytest.fixture
def sample_processed_data():
    """Create a minimal valid processed dataset for testing."""
    data = {
        'strain_rate': [0.1, 0.2, 0.3, 0.4, 0.5],
        'temperature': [300, 350, 400, 450, 500],
        'alloy_family': ['Al', 'Al', 'Cu', 'Cu', 'Cu'],
        'ODF_{100}': [0.5, 0.6, 0.7, 0.8, 0.9],
        'ODF_{110}': [0.4, 0.5, 0.6, 0.7, 0.8],
        'ODF_{111}': [0.3, 0.4, 0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    return df


def test_load_processed_data(sample_processed_data, tmp_path):
    """Test that load_processed_data correctly splits features and targets."""
    # Save sample data
    csv_path = tmp_path / "processed_dataset.csv"
    sample_processed_data.to_csv(csv_path, index=False)
    
    # Load
    X, y = trainer.load_processed_data(str(csv_path))
    
    # Assertions
    assert X.shape[0] == 5
    assert y.shape[0] == 5
    assert 'strain_rate' in X.columns
    assert 'ODF_{100}' in y.columns
    assert 'ODF_{111}' in y.columns
    assert list(X.columns) == ['strain_rate', 'temperature', 'alloy_family']


def test_load_processed_data_missing_file():
    """Test that load_processed_data raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        trainer.load_processed_data("non_existent_path.csv")


@patch('code.models.trainer.GridSearchCV')
@patch('code.models.trainer.RandomForestRegressor')
def test_run_grid_search(mock_rf, mock_grid, sample_processed_data, tmp_path):
    """Test that run_grid_search executes with correct parameters."""
    # Setup mocks
    mock_instance = MagicMock()
    mock_instance.best_params_ = {'n_estimators': 100}
    mock_instance.best_score_ = 0.85
    mock_grid.return_value = mock_instance
    mock_rf.return_value = MagicMock()
    
    # Prepare data
    csv_path = tmp_path / "processed_dataset.csv"
    sample_processed_data.to_csv(csv_path, index=False)
    X, y = trainer.load_processed_data(str(csv_path))
    
    # Run
    model, results = trainer.run_grid_search(X, y)
    
    # Verify GridSearchCV was called
    assert mock_grid.called
    call_args = mock_grid.call_args
    assert call_args[1]['cv'] == 5
    assert 'n_estimators' in call_args[1]['param_grid']


def test_evaluate_model(sample_processed_data, tmp_path):
    """Test metric calculation."""
    # Create a simple mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([
        [0.5, 0.4, 0.3],
        [0.6, 0.5, 0.4],
        [0.7, 0.6, 0.5],
        [0.8, 0.7, 0.6],
        [0.9, 0.8, 0.7]
    ])
    
    csv_path = tmp_path / "processed_dataset.csv"
    sample_processed_data.to_csv(csv_path, index=False)
    X, y = trainer.load_processed_data(str(csv_path))
    
    metrics = trainer.evaluate_model(mock_model, X, y)
    
    assert 'r2_mean' in metrics
    assert 'r2_per_output' in metrics
    assert metrics['n_samples'] == 5


def test_save_model_and_results(tmp_path):
    """Test that artifacts are saved correctly."""
    mock_model = MagicMock()
    search_results = {
        "best_params": {"n_estimators": 50},
        "best_score": 0.8,
        "total_time_seconds": 10.0,
        "timeout_reached": False
    }
    eval_metrics = {
        "r2_mean": 0.85,
        "r2_per_output": {"ODF_{100}": 0.85}
    }
    
    model_path = str(tmp_path / "model.json")
    metrics_path = str(tmp_path / "metrics.json")
    
    trainer.save_model_and_results(mock_model, search_results, eval_metrics, model_path, metrics_path)
    
    # Check JSON file exists and has content
    assert os.path.exists(metrics_path)
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    assert data['best_params']['n_estimators'] == 50
    assert data['training_metrics']['r2_mean'] == 0.85
    
    # Check model binary exists (either .pkl or .joblib)
    pkl_path = model_path.replace('.json', '.pkl')
    assert os.path.exists(pkl_path)


def test_train_pipeline_integration(sample_processed_data, tmp_path):
    """Integration test for the full training pipeline."""
    csv_path = str(tmp_path / "processed_dataset.csv")
    model_path = str(tmp_path / "model.json")
    metrics_path = str(tmp_path / "metrics.json")
    
    sample_processed_data.to_csv(csv_path, index=False)
    
    # Patch GridSearchCV to avoid long runtime in tests
    with patch('code.models.trainer.GridSearchCV') as mock_grid:
        mock_instance = MagicMock()
        mock_instance.best_params_ = {'n_estimators': 10}
        mock_instance.best_score_ = 0.9
        mock_instance.cv_results_ = pd.DataFrame({'params': [{}], 'mean_test_score': [0.9]})
        mock_grid.return_value = mock_instance
        
        # Patch RandomForestRegressor
        with patch('code.models.trainer.RandomForestRegressor'):
            result = trainer.train_pipeline(
                data_path=csv_path,
                model_output=model_path,
                metrics_output=metrics_path
            )
    
    assert result['status'] == 'success'
    assert 'metrics' in result
    assert os.path.exists(metrics_path)