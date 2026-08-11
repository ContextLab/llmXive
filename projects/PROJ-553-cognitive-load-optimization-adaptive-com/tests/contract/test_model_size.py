import os
import pickle
import pytest
from pathlib import Path

def test_model_file_exists():
    """Test that the model file is created after training."""
    model_path = "data/processed/load_model.pkl"
    assert os.path.exists(model_path), f"Model file not found at {model_path}"

def test_model_size_within_limit():
    """Test that the model file size is within the 500 MB limit."""
    model_path = "data/processed/load_model.pkl"
    size_limit_mb = 500
    
    assert os.path.exists(model_path), f"Model file not found at {model_path}"
    
    file_size_bytes = os.path.getsize(model_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    assert file_size_mb <= size_limit_mb, \
        f"Model size {file_size_mb:.2f} MB exceeds limit of {size_limit_mb} MB"

def test_model_loads_successfully():
    """Test that the model can be loaded without errors."""
    model_path = "data/processed/load_model.pkl"
    
    assert os.path.exists(model_path), f"Model file not found at {model_path}"
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Basic check that it's a valid LightGBM model
        assert model is not None
        assert hasattr(model, 'predict')
    except Exception as e:
        pytest.fail(f"Failed to load model: {e}")

def test_metrics_file_exists():
    """Test that the metrics file is created."""
    metrics_path = "data/processed/model_metrics.json"
    assert os.path.exists(metrics_path), f"Metrics file not found at {metrics_path}"

def test_metrics_contains_required_fields():
    """Test that the metrics file contains required fields."""
    import json
    metrics_path = "data/processed/model_metrics.json"
    
    assert os.path.exists(metrics_path), f"Metrics file not found at {metrics_path}"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    required_fields = ['pearson_correlation', 'model_size_mb', 'model_size_limit_mb', 'size_check_passed']
    
    for field in required_fields:
        assert field in metrics, f"Missing required field: {field}"

def test_size_check_passed():
    """Test that the size check passed in metrics."""
    import json
    metrics_path = "data/processed/model_metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert metrics.get('size_check_passed', False), "Size check did not pass"
