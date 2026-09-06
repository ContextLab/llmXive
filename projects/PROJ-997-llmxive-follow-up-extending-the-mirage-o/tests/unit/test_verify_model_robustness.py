"""
Unit tests for T042: verify_model_robustness.py
"""
import json
import tempfile
import os
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import KernelRidge
from unittest.mock import patch, MagicMock

# Import the module functions
from cli.verify_model_robustness import (
    load_model, 
    load_test_data, 
    perturb_features, 
    calculate_robustness_metrics,
    main
)

@pytest.fixture
def temp_model_file():
    """Create a temporary KRR model file."""
    model = KernelRidge(kernel='rbf', alpha=0.1)
    # Dummy fit to make it valid
    X_dummy = np.random.rand(10, 2)
    y_dummy = np.random.rand(10)
    model.fit(X_dummy, y_dummy)
    
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        import pickle
        pickle.dump(model, f)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_test_data_file():
    """Create a temporary parquet test file."""
    df = pd.DataFrame({
        'gradient_norms': np.random.rand(20),
        'local_curvature': np.random.rand(20),
        'calculated_kl_divergence': np.random.rand(20)
    })
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        df.to_parquet(f.name)
        path = f.name
    yield path
    os.unlink(path)

def test_load_model_success(temp_model_file):
    model = load_model(Path(temp_model_file))
    assert isinstance(model, KernelRidge)

def test_load_model_not_found():
    with pytest.raises(FileNotFoundError):
        load_model(Path("/nonexistent/path.pkl"))

def test_load_test_data_success(temp_test_data_file):
    X, y, features = load_test_data(Path(temp_test_data_file))
    assert X.shape[0] == 20
    assert len(features) == 2
    assert 'gradient_norms' in features or 'local_curvature' in features

def test_load_test_data_not_found():
    with pytest.raises(FileNotFoundError):
        load_test_data(Path("/nonexistent.parquet"))

def test_perturb_features_basic():
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    perturbations = perturb_features(X, 0.05, seed=42)
    assert len(perturbations) == 2 # +5% and -5%
    
    # Check +5%
    X_plus = perturbations[0]
    expected_plus = X * 1.05
    assert np.allclose(X_plus, expected_plus)
    
    # Check -5%
    X_minus = perturbations[1]
    expected_minus = X * 0.95
    assert np.allclose(X_minus, expected_minus)

def test_calculate_robustness_metrics():
    # Create a simple model
    model = KernelRidge(kernel='linear', alpha=0.1)
    X_train = np.random.rand(10, 2)
    y_train = np.random.rand(10)
    model.fit(X_train, y_train)
    
    X_test = np.random.rand(5, 2)
    y_test = np.random.rand(5)
    
    perturbations = perturb_features(X_test, 0.05, seed=42)
    features = ['f1', 'f2']
    
    metrics = calculate_robustness_metrics(model, X_test, y_test, perturbations, features)
    
    assert "original_mean" in metrics
    assert "perturbation_analysis" in metrics
    assert len(metrics["perturbation_analysis"]) == 2
    assert "summary" in metrics
    assert "average_coefficient_of_variation" in metrics["summary"]

def test_main_execution(temp_model_file, temp_test_data_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "robustness.json")
        
        # Mock argparse to avoid sys.argv issues
        with patch('sys.argv', ['script', '--model-path', temp_model_file, '--test-data', temp_test_data_file, '--output', output_path]):
            result = main()
        
        assert result == 0
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "task_id" in data
        assert data["task_id"] == "T042"
        assert "summary" in data