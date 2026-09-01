import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
import tempfile
import json

# Import the module to test
# We need to mock the config paths to avoid needing real data for unit tests
from train_models import train_and_evaluate, load_training_data, save_model

@pytest.fixture
def mock_data():
    """Generate mock feature matrix and target vector."""
    np.random.seed(42)
    X = np.random.rand(100, 8)
    y = np.random.rand(100)
    return X, y

@pytest.fixture
def mock_df():
    """Generate a mock DataFrame for load_training_data simulation."""
    df = pd.DataFrame({
        'mean_atomic_radius': np.random.rand(50),
        'var_atomic_radius': np.random.rand(50),
        'mean_electronegativity': np.random.rand(50),
        'var_electronegativity': np.random.rand(50),
        'mean_VEC': np.random.rand(50),
        'var_VEC': np.random.rand(50),
        'mean_melting_point': np.random.rand(50),
        'var_melting_point': np.random.rand(50),
        'target_energy': np.random.rand(50)
    })
    return df

def test_train_and_evaluate_random_forest(mock_data):
    """Test that RandomForestRegressor trains and returns valid metrics."""
    from sklearn.ensemble import RandomForestRegressor
    X, y = mock_data
    
    result = train_and_evaluate(
        X, y, 
        RandomForestRegressor, 
        "RandomForestRegressor", 
        {"n_estimators": 5, "max_depth": 3} # Small params for speed
    )
    
    assert "model_name" in result
    assert result["model_name"] == "RandomForestRegressor"
    assert "mean_cv_r2" in result
    assert isinstance(result["mean_cv_r2"], float)
    assert "model_object" in result
    assert result["model_object"] is not None
    assert result["execution_time_sec"] > 0

def test_train_and_evaluate_gradient_boosting(mock_data):
    """Test that GradientBoostingRegressor trains and returns valid metrics."""
    from sklearn.ensemble import GradientBoostingRegressor
    X, y = mock_data
    
    result = train_and_evaluate(
        X, y, 
        GradientBoostingRegressor, 
        "GradientBoostingRegressor", 
        {"n_estimators": 5, "max_depth": 2} # Small params for speed
    )
    
    assert "model_name" in result
    assert result["model_name"] == "GradientBoostingRegressor"
    assert "mean_cv_r2" in result
    assert isinstance(result["mean_cv_r2"], float)
    assert result["std_cv_r2"] >= 0

def test_save_model_creates_files(mock_data, tmp_path):
    """Test that save_model creates the expected .pkl and .json files."""
    from sklearn.ensemble import RandomForestRegressor
    X, y = mock_data
    
    result = train_and_evaluate(
        X, y, 
        RandomForestRegressor, 
        "TestModel", 
        {"n_estimators": 1}
    )
    
    save_model(result, tmp_path)
    
    # Check for model file
    model_file = tmp_path / "testmodel_model.pkl"
    assert model_file.exists()
    
    # Check for metadata file
    meta_file = tmp_path / "testmodel_metadata.json"
    assert meta_file.exists()
    
    # Verify metadata content
    with open(meta_file, 'r') as f:
        meta = json.load(f)
    
    assert "mean_cv_r2" in meta
    assert "params" in meta
    assert meta["random_seed"] == 42

def test_load_training_data_missing_file(tmp_path):
    """Test that load_training_data raises FileNotFoundError if data is missing."""
    # Temporarily override DATA_PROCESSED
    import train_models
    original_path = train_models.DATA_PROCESSED
    train_models.DATA_PROCESSED = tmp_path # Empty dir
    
    with pytest.raises(FileNotFoundError):
        load_training_data()
    
    # Restore
    train_models.DATA_PROCESSED = original_path
