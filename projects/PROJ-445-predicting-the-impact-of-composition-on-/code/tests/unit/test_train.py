import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the project root to avoid path issues in tests
@pytest.fixture
def temp_project_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create directory structure
        (root / "data" / "processed").mkdir(parents=True)
        (root / "data" / "split").mkdir(parents=True)
        (root / "state").mkdir(parents=True)
        (root / "artifacts").mkdir(parents=True)
        (root / "data" / "residualized").mkdir(parents=True)
        yield root

@pytest.fixture
def sample_data(temp_project_root):
    # Create sample train/test data
    train_df = pd.DataFrame({
        'composition': ['Si0.2Se0.8', 'As0.3Se0.7'],
        'Tg': [200.0, 250.0],
        'mean_coordination': [2.4, 2.5],
        'electronegativity_variance': [0.1, 0.2],
        'atomic_radius_variance': [0.05, 0.06]
    })
    test_df = pd.DataFrame({
        'composition': ['Ge0.3Se0.7'],
        'Tg': [300.0],
        'mean_coordination': [2.6],
        'electronegativity_variance': [0.15],
        'atomic_radius_variance': [0.07]
    })
    
    train_path = temp_project_root / "data" / "processed" / "train.csv"
    test_path = temp_project_root / "data" / "processed" / "test.csv"
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    return train_df, test_df

def test_linear_baseline_training(sample_data, temp_project_root):
    """Test that Linear Regression baseline trains and produces metrics."""
    from src.models.train import train_linear_baseline
    
    X_train = sample_data[0][['mean_coordination', 'electronegativity_variance', 'atomic_radius_variance']].values
    y_train = sample_data[0]['Tg'].values
    X_test = sample_data[1][['mean_coordination', 'electronegativity_variance', 'atomic_radius_variance']].values
    y_test = sample_data[1]['Tg'].values
    
    model, metrics = train_linear_baseline(X_train, y_train, X_test, y_test)
    
    assert model is not None
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['r2'], float)
    assert metrics['model_type'] == 'LinearRegression'

def test_gradient_boosting_training(sample_data, temp_project_root):
    """Test that Gradient Boosting trains and produces metrics."""
    from src.models.train import train_gradient_boosting
    
    X_train = sample_data[0][['mean_coordination', 'electronegativity_variance', 'atomic_radius_variance']].values
    y_train = sample_data[0]['Tg'].values
    X_test = sample_data[1][['mean_coordination', 'electronegativity_variance', 'atomic_radius_variance']].values
    y_test = sample_data[1]['Tg'].values
    
    model, metrics = train_gradient_boosting(X_train, y_train, X_test, y_test)
    
    assert model is not None
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert 'cv_r2_mean' in metrics
    assert 'best_params' in metrics
    assert metrics['model_type'] == 'GradientBoostingRegressor'

def test_cpu_only_compliance(temp_project_root):
    """Test that the training logic enforces CPU mode."""
    from src.utils.cpu_compliance import enforce_cpu_mode
    
    # This is a basic check that the function exists and runs
    result = enforce_cpu_mode()
    assert result is True or result is None # Depends on implementation

def test_data_loading_error_handling(temp_project_root):
    """Test that error is raised if data files are missing."""
    from src.models.train import load_split_data
    
    # Ensure files don't exist
    train_path = temp_project_root / "data" / "processed" / "train.csv"
    test_path = temp_project_root / "data" / "processed" / "test.csv"
    
    if train_path.exists(): train_path.unlink()
    if test_path.exists(): test_path.unlink()
    
    with pytest.raises(FileNotFoundError):
        load_split_data()
