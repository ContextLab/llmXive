import pytest
import json
import os
import tempfile
import pickle
import numpy as np
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, 'projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code')
from train import load_features, prepare_data, train_and_evaluate, run_cross_validation, save_results

@pytest.fixture
def sample_features():
    """Create sample features data for testing."""
    return [
        {
            'sample_id': 'sample_1',
            'variance': 0.5,
            'entropy': 1.2,
            'skewness': 0.1,
            'kurtosis': 2.5,
            'entanglement_score': 1.8,
            'global_eigenvalue': 2.3,
            'fidelity_loss': 0.3
        },
        {
            'sample_id': 'sample_2',
            'variance': 0.8,
            'entropy': 1.5,
            'skewness': -0.2,
            'kurtosis': 3.1,
            'entanglement_score': 2.1,
            'global_eigenvalue': 2.3,
            'fidelity_loss': 0.5
        },
        {
            'sample_id': 'sample_3',
            'variance': 0.3,
            'entropy': 0.9,
            'skewness': 0.3,
            'kurtosis': 2.0,
            'entanglement_score': 1.5,
            'global_eigenvalue': 2.3,
            'fidelity_loss': 0.2
        },
        {
            'sample_id': 'sample_4',
            'variance': 0.6,
            'entropy': 1.3,
            'skewness': 0.0,
            'kurtosis': 2.8,
            'entanglement_score': 1.9,
            'global_eigenvalue': 2.3,
            'fidelity_loss': 0.4
        },
        {
            'sample_id': 'sample_5',
            'variance': 0.4,
            'entropy': 1.1,
            'skewness': 0.15,
            'kurtosis': 2.4,
            'entanglement_score': 1.7,
            'global_eigenvalue': 2.3,
            'fidelity_loss': 0.25
        }
    ]

@pytest.fixture
def temp_features_file(sample_features):
    """Create a temporary features JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_features, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_features_success(temp_features_file):
    """Test successful loading of features from JSON file."""
    features = load_features(temp_features_file)
    assert len(features) == 5
    assert 'sample_id' in features[0]
    assert 'fidelity_loss' in features[0]

def test_load_features_not_found():
    """Test loading from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_features('non_existent_file.json')

def test_load_features_empty():
    """Test loading from empty file raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_features(temp_path)
    finally:
        os.unlink(temp_path)

def test_prepare_data(temp_features_file):
    """Test data preparation extracts features and target correctly."""
    features = load_features(temp_features_file)
    X, y, sample_ids = prepare_data(features)
    
    assert len(X) == 5
    assert len(y) == 5
    assert len(sample_ids) == 5
    assert X.shape[1] == 6  # 6 feature columns
    assert all(isinstance(sid, str) for sid in sample_ids)

def test_prepare_data_missing_target():
    """Test that samples with missing targets are filtered out."""
    features = [
        {'sample_id': '1', 'variance': 0.5, 'entropy': 1.2, 'skewness': 0.1, 
         'kurtosis': 2.5, 'entanglement_score': 1.8, 'global_eigenvalue': 2.3, 'fidelity_loss': 0.3},
        {'sample_id': '2', 'variance': 0.8, 'entropy': 1.5, 'skewness': -0.2, 
         'kurtosis': 3.1, 'entanglement_score': 2.1, 'global_eigenvalue': 2.3, 'fidelity_loss': None},
        {'sample_id': '3', 'variance': 0.3, 'entropy': 0.9, 'skewness': 0.3, 
         'kurtosis': 2.0, 'entanglement_score': 1.5, 'global_eigenvalue': 2.3, 'fidelity_loss': 0.2}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(features, f)
        temp_path = f.name
    
    try:
        loaded_features = load_features(temp_path)
        X, y, sample_ids = prepare_data(loaded_features)
        
        assert len(X) == 2  # One sample filtered out
        assert len(y) == 2
    finally:
        os.unlink(temp_path)

def test_train_and_evaluate(temp_features_file):
    """Test model training and evaluation."""
    features = load_features(temp_features_file)
    X, y, _ = prepare_data(features)
    
    model, metrics = train_and_evaluate(X, y, test_size=0.2, random_state=42)
    
    assert model is not None
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert metrics['train_size'] + metrics['test_size'] == len(X)
    assert metrics['test_size'] == int(len(X) * 0.2)

def test_run_cross_validation(temp_features_file):
    """Test cross-validation execution."""
    features = load_features(temp_features_file)
    X, y, _ = prepare_data(features)
    
    # Create a simple model for CV
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    cv_results = run_cross_validation(model, X, y, cv_folds=3)
    
    assert 'cv_scores' in cv_results
    assert 'mean_cv_r2' in cv_results
    assert 'std_cv_r2' in cv_results
    assert len(cv_results['cv_scores']) == 3

def test_save_results(temp_features_file):
    """Test saving model and results to disk."""
    features = load_features(temp_features_file)
    X, y, _ = prepare_data(features)
    
    model, metrics = train_and_evaluate(X, y, test_size=0.2, random_state=42)
    cv_results = run_cross_validation(model, X, y)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'results.json')
        model_path, results_path = save_results(model, metrics, cv_results, output_path)
        
        # Check model file exists
        assert os.path.exists(model_path)
        assert model_path.endswith('model.pkl')
        
        # Check results file exists
        assert os.path.exists(results_path)
        
        # Verify model can be loaded
        with open(model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        assert loaded_model is not None
        
        # Verify results content
        with open(results_path, 'r') as f:
            results = json.load(f)
        assert 'metrics' in results
        assert 'cross_validation' in results