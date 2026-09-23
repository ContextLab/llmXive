"""
Unit tests for SHAP computation functionality.
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from interpret import compute_shap_values, load_best_model, load_processed_data, prepare_features_targets
from seed import set_seed

@pytest.fixture
def sample_model():
    """Create a simple mock model for testing."""
    # Create a simple sklearn model for testing
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    return model

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    data = {
        'power': np.random.uniform(100, 500, n_samples),
        'scanning_speed': np.random.uniform(100, 1000, n_samples),
        'pulse_duration': np.random.uniform(10, 100, n_samples),
        'hardness': np.random.uniform(200, 800, n_samples),
        'wear_coefficient': np.random.uniform(0.001, 0.1, n_samples),
        'normalization_method': ['normalized'] * n_samples
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        models_dir = tmpdir / "models"
        data_dir = tmpdir / "data" / "processed"
        reports_dir = tmpdir / "reports"
        state_dir = tmpdir / "state"
        
        models_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        
        yield {
            'tmpdir': tmpdir,
            'models_dir': models_dir,
            'data_dir': data_dir,
            'reports_dir': reports_dir,
            'state_dir': state_dir
        }

def test_prepare_features_targets(sample_data):
    """Test feature and target preparation."""
    X, y, feature_names = prepare_features_targets(sample_data, target_col='wear_coefficient')
    
    assert X.shape[0] == len(sample_data)
    assert len(feature_names) == 4  # power, scanning_speed, pulse_duration, hardness
    assert y is not None
    assert len(y) == len(sample_data)

@patch('interpret.joblib')
def test_compute_shap_values_with_mock_model(mock_joblib, sample_model, sample_data, temp_dirs):
    """Test SHAP computation with mocked model loading."""
    # Mock joblib.load to return our sample model
    mock_joblib.load.return_value = sample_model
    
    # Save sample data to temp directory
    data_path = temp_dirs['data_dir'] / "normalized_only.csv"
    sample_data.to_csv(data_path, index=False)
    
    # Mock SHAP to avoid actual computation
    with patch('interpret.shap') as mock_shap:
        # Setup mock SHAP values
        mock_shap_values = np.random.rand(100, 4)
        mock_shap.TreeExplainer.return_value.shap_values.return_value = mock_shap_values
        
        # Mock model type to trigger TreeExplainer
        sample_model.__class__.__name__ = 'RandomForestRegressor'
        
        result = compute_shap_values(
            model=sample_model,
            data_path=data_path,
            model_path=temp_dirs['models_dir'] / "best_model.joblib",
            output_path=temp_dirs['data_dir'] / "shap_values.npy"
        )
        
        assert result['status'] == 'success'
        assert result['n_samples'] == 100
        assert result['n_features'] == 4
        assert 'feature_names' in result
        assert 'feature_importance_rank' in result

def test_compute_shap_values_missing_data(sample_data, temp_dirs):
    """Test error handling when data file is missing."""
    with pytest.raises(FileNotFoundError):
        compute_shap_values(
            data_path=temp_dirs['data_dir'] / "nonexistent.csv",
            model_path=temp_dirs['models_dir'] / "best_model.joblib"
        )

def test_compute_shap_values_missing_model(temp_dirs):
    """Test error handling when model file is missing."""
    # Create sample data
    data_path = temp_dirs['data_dir'] / "normalized_only.csv"
    sample_data = pd.DataFrame({
        'power': [100, 200],
        'wear_coefficient': [0.01, 0.02]
    })
    sample_data.to_csv(data_path, index=False)
    
    with pytest.raises(FileNotFoundError):
        compute_shap_values(
            data_path=data_path,
            model_path=temp_dirs['models_dir'] / "nonexistent.joblib"
        )

@patch('interpret.shap')
def test_compute_shap_values_error_handling(mock_shap, sample_model, sample_data, temp_dirs):
    """Test error handling when SHAP computation fails."""
    # Save sample data
    data_path = temp_dirs['data_dir'] / "normalized_only.csv"
    sample_data.to_csv(data_path, index=False)
    
    # Mock SHAP to raise an error
    mock_shap.TreeExplainer.return_value.shap_values.side_effect = Exception("SHAP error")
    
    with pytest.raises(ValueError, match="Failed to compute SHAP values"):
        compute_shap_values(
            model=sample_model,
            data_path=data_path,
            model_path=temp_dirs['models_dir'] / "best_model.joblib"
        )