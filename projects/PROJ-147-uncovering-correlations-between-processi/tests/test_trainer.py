"""
Unit tests for the trainer module.
"""
import os
import tempfile
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the module under test
from code.models.trainer import (
    load_processed_data,
    get_param_distributions,
    train_model,
    run_training_pipeline
)

@pytest.fixture
def sample_processed_data():
    """Create a temporary CSV with sample processed data."""
    data = {
        'rolling_temp': np.random.uniform(300, 800, 100),
        'strain_rate': np.random.uniform(0.1, 10.0, 100),
        'reduction_ratio': np.random.uniform(0.1, 0.8, 100),
        'odf_100': np.random.uniform(1.0, 5.0, 100),
        'odf_110': np.random.uniform(1.0, 5.0, 100),
        'odf_111': np.random.uniform(1.0, 5.0, 100),
        'alloy_family': np.random.choice(['Al', 'Mg', 'Ti'], 100)
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for model output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_get_param_distributions():
    """Test that param distributions are valid and non-empty."""
    dist = get_param_distributions()
    assert isinstance(dist, dict)
    assert 'n_estimators' in dist
    assert 'max_depth' in dist
    assert len(dist['n_estimators']) > 0
    assert len(dist['max_depth']) > 0

def test_load_processed_data(sample_processed_data):
    """Test loading and splitting of processed data."""
    X, y, targets = load_processed_data(sample_processed_data)
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.DataFrame)
    assert len(targets) == 3
    assert 'odf_100' in targets
    assert 'odf_110' in targets
    assert 'odf_111' in targets
    assert len(X) == 100
    assert len(y) == 100
    assert list(X.columns) == ['rolling_temp', 'strain_rate', 'reduction_ratio']

def test_train_model_basic(sample_processed_data, temp_output_dir):
    """Test basic model training with reduced iterations for speed."""
    X, y, targets = load_processed_data(sample_processed_data)
    
    # Override n_iter to speed up test
    import code.models.trainer as trainer_module
    original_n_iter = trainer_module.N_ITERATIONS
    trainer_module.N_ITERATIONS = 2  # Very small for unit test
    
    try:
        model, metrics = train_model(X, y, targets, temp_output_dir, timeout_seconds=300)
        
        assert model is not None
        assert isinstance(metrics, dict)
        assert 'best_params' in metrics
        assert 'best_cv_score' in metrics
        assert 'training_time_seconds' in metrics
        
        # Check files were created
        assert os.path.exists(os.path.join(temp_output_dir, "best_model.pkl"))
        assert os.path.exists(os.path.join(temp_output_dir, "training_metrics.json"))
        
        # Verify metrics content
        with open(os.path.join(temp_output_dir, "training_metrics.json")) as f:
            saved_metrics = json.load(f)
            assert saved_metrics['best_cv_score'] == metrics['best_cv_score']
    finally:
        trainer_module.N_ITERATIONS = original_n_iter

def test_run_training_pipeline(sample_processed_data, temp_output_dir):
    """Test the full pipeline orchestration."""
    import code.models.trainer as trainer_module
    original_n_iter = trainer_module.N_ITERATIONS
    trainer_module.N_ITERATIONS = 2
    
    try:
        results = run_training_pipeline(sample_processed_data, temp_output_dir)
        
        assert 'model_path' in results
        assert 'metrics' in results
        assert 'target_names' in results
        assert os.path.exists(results['model_path'])
    finally:
        trainer_module.N_ITERATIONS = original_n_iter

def test_missing_data_file():
    """Test error handling for missing data file."""
    with pytest.raises(FileNotFoundError):
        load_processed_data("non_existent_file.csv")

def test_empty_data():
    """Test handling of empty or invalid data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n") # Header only
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_processed_data(temp_path)
    finally:
        os.unlink(temp_path)