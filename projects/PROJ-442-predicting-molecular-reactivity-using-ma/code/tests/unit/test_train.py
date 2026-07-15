import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

# Mock the external dependencies that require heavy data loading or config files
from unittest.mock import patch, MagicMock

from src.modeling.train import (
    load_target_data,
    normalize_target,
    run_training_pipeline
)

@pytest.fixture
def temp_feature_file():
    """Create a temporary parquet file with mock feature data."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        df = pd.DataFrame({
            'feature_1': np.random.rand(100),
            'feature_2': np.random.rand(100),
            'feature_3': np.random.rand(100),
            'target': np.random.rand(100) * 100
        })
        df.to_parquet(tmp.name)
        yield Path(tmp.name)
        os.unlink(tmp.name)

@pytest.fixture
def mock_config():
    """Return a mock configuration dictionary."""
    return {
        'model': {
            'xgboost': {
                'n_estimators': 10,
                'max_depth': 3,
                'learning_rate': 0.1
            }
        }
    }

def test_load_target_data(temp_feature_file):
    """Test loading features and target from parquet."""
    X, y = load_target_data(temp_feature_file)
    assert X.shape[0] == 100
    assert X.shape[1] == 3
    assert len(y) == 100
    assert 'target' not in X.columns

def test_normalize_target():
    """Test Z-score normalization."""
    y = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    y_norm, params = normalize_target(y)
    
    # Check mean is approx 0
    assert np.isclose(y_norm.mean(), 0.0, atol=1e-5)
    # Check std is approx 1
    assert np.isclose(y_norm.std(), 1.0, atol=1e-5)
    # Check params
    assert 'mean' in params
    assert 'std' in params

def test_run_training_pipeline(temp_feature_file, mock_config, tmp_path):
    """Test the full training pipeline end-to-end with mocked config loading."""
    model_path = tmp_path / "model.json"
    log_path = tmp_path / "log.json"
    config_path = tmp_path / "config.yaml"

    # Write a dummy config file
    with open(config_path, 'w') as f:
        f.write("model:\n  xgboost:\n    n_estimators: 5\n")

    # Mock load_config to return our mock_config instead of reading file
    with patch('src.modeling.train.load_config', return_value=mock_config):
        # Mock the update_stage_status and register_artifact to avoid state file issues in tests
        with patch('src.modeling.train.update_stage_status'), \
             patch('src.modeling.train.register_artifact'):
            
            result = run_training_pipeline(
                features_path=temp_feature_file,
                output_model_path=model_path,
                output_log_path=log_path,
                config_path=config_path
            )

    assert model_path.exists()
    assert log_path.exists()
    assert result['status'] == 'success'
    assert 'training_score_r2' in result
    assert result['samples'] == 100
    assert result['features'] == 3