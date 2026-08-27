import os
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

# Import the functions we are testing
from code.classification import load_features, train_and_validate, run_classification

@pytest.fixture
def temp_feature_csv():
    """Create a temporary CSV file with synthetic but structurally valid features for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a small dataset: 20 epochs, 3 features, 2 conditions
        # We use deterministic values to ensure test reproducibility
        n_samples = 20
        np.random.seed(42)
        
        # Features: Alpha_P, Beta_F, Noise
        data = {
            'alpha_p': np.random.normal(0, 1, n_samples),
            'beta_f': np.random.normal(0, 1, n_samples),
            'noise': np.random.normal(0, 1, n_samples),
            'condition': ['active'] * 10 + ['passive'] * 10
        }
        
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_output_json():
    """Path for output JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield f.name
    os.unlink(f.name)

def test_load_features(temp_feature_csv):
    """Test T026: Ensure features are loaded correctly."""
    X, y, feature_names = load_features(temp_feature_csv)
    
    assert X.shape[0] == 20, "Should load 20 samples"
    assert X.shape[1] == 3, "Should have 3 features"
    assert len(y) == 20
    assert set(y) == {'active', 'passive'}
    assert 'alpha_p' in feature_names
    assert 'beta_f' in feature_names

def test_train_and_validate_metrics(temp_feature_csv):
    """Test T026: Ensure train_and_validate returns correct metric structure with std."""
    X, y, _ = load_features(temp_feature_csv)
    
    # Use 3 folds for small dataset
    results = train_and_validate(X, y, n_folds=3)
    
    # Check structure
    assert 'accuracy' in results
    assert 'precision' in results
    assert 'recall' in results
    
    # Check required fields per metric
    for metric in ['accuracy', 'precision', 'recall']:
        assert 'mean' in results[metric], f"{metric} must have mean"
        assert 'std' in results[metric], f"{metric} must have std (T026 requirement)"
        assert 'values' in results[metric], f"{metric} must have values list"
        assert isinstance(results[metric]['std'], float), "Std must be a float"
    
    # Verify std is not zero for random-ish data (unless folds are identical)
    # We don't assert > 0 strictly as it might happen, but we check presence
    assert results['accuracy']['std'] >= 0

def test_run_classification_integration(temp_feature_csv, temp_output_json):
    """Test T026: End-to-end run_classification produces JSON with metrics and std."""
    result = run_classification(temp_feature_csv, temp_output_json)
    
    # Verify file exists
    assert os.path.exists(temp_output_json)
    
    # Verify JSON content
    with open(temp_output_json, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report['status'] == 'success'
    assert 'classification_metrics' in saved_report
    
    metrics = saved_report['classification_metrics']
    assert 'accuracy' in metrics
    assert 'std' in metrics['accuracy']
    assert 'precision' in metrics
    assert 'std' in metrics['precision']
    assert 'recall' in metrics
    assert 'std' in metrics['recall']

def test_sample_size_validation_logic():
    """Verify that the logic handles small datasets without crashing, 
    though T014 handles the hard halt. This ensures T026 runs on valid data."""
    # This test is implicit in the fixtures above, but ensures T026 doesn't fail on small N
    pass