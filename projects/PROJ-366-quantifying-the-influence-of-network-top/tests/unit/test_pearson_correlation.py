"""
Unit tests for Pearson Correlation Analysis (T033a).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Import the module under test
# Note: We assume the test is run from the project root or code is in PYTHONPATH
from analysis.pearson_correlation import (
    load_feature_importance_data,
    load_thermal_conductivity_data,
    align_data,
    compute_pearson_correlation,
    generate_correlation_report,
    save_results
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        yield tmp_path

def test_load_feature_importance_data(temp_dirs):
    """Test loading SHAP values from a numpy file."""
    shap_path = temp_dirs / "shap_values.npy"
    
    # Create dummy data: 10 samples, 5 features
    dummy_shap = np.random.rand(10, 5)
    np.save(shap_path, dummy_shap)
    
    # Create dummy feature names
    meta_path = temp_dirs / "shap_values.json"
    with open(meta_path, 'w') as f:
        json.dump({'feature_names': ['f1', 'f2', 'f3', 'f4', 'f5']}, f)
    
    values, names = load_feature_importance_data(shap_path)
    
    assert values.shape == (10, 5)
    assert names == ['f1', 'f2', 'f3', 'f4', 'f5']

def test_load_thermal_conductivity_data(temp_dirs):
    """Test loading conductivity from JSON files."""
    # Create sample JSON files
    for i in range(3):
        sample_data = {
            'graph_id': f'sample_{i}',
            'conductivity': 1.5 + i * 0.1,
            'converged': True
        }
        with open(temp_dirs / f'sample_{i}.json', 'w') as f:
            json.dump(sample_data, f)
    
    conductivity_map = load_thermal_conductivity_data(temp_dirs)
    
    assert len(conductivity_map) == 3
    assert 'sample_0' in conductivity_map
    assert abs(conductivity_map['sample_0'] - 1.5) < 1e-6

def test_align_data(temp_dirs):
    """Test aligning SHAP and conductivity data."""
    # 5 samples, 3 features
    shap_vals = np.random.rand(5, 3)
    feature_names = ['a', 'b', 'c']
    
    # Conductivity for 3 of the 5 samples
    conductivity_map = {
        's1': 1.0,
        's2': 2.0,
        's3': 3.0
    }
    
    # Sample IDs corresponding to shap_vals rows
    sample_ids = ['s1', 's2', 's4', 's3', 's5']
    
    aligned_shap, aligned_cond, valid_indices = align_data(
        shap_vals, feature_names, conductivity_map, sample_ids
    )
    
    # Should have 3 valid samples (s1, s2, s3)
    assert len(valid_indices) == 3
    assert aligned_shap.shape == (3, 3)
    assert len(aligned_cond) == 3

def test_compute_pearson_correlation():
    """Test Pearson correlation calculation."""
    # Perfect positive correlation
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])
    
    shap_vals = x.reshape(1, -1) # 1 sample, 5 features? No, need N samples.
    # Reshape to N samples, 1 feature for simplicity in this test
    shap_vals = x.reshape(-1, 1)
    cond = y.reshape(-1)
    
    results = compute_pearson_correlation(shap_vals, cond)
    
    assert 0 in results
    assert abs(results[0]['r']) > 0.99
    assert results[0]['p_value'] < 0.05

def test_generate_correlation_report():
    """Test report generation."""
    results = {
        0: {'r': 0.9, 'p_value': 0.01, 'n': 10},
        1: {'r': -0.5, 'p_value': 0.05, 'n': 10}
    }
    feature_names = ['feat_a', 'feat_b']
    
    report = generate_correlation_report(results, feature_names, 10)
    
    assert report['method'] == 'pearson'
    assert report['n_samples'] == 10
    assert len(report['results']) == 2
    # Check sorting (absolute value)
    assert report['results'][0]['feature'] == 'feat_a'

def test_save_results(temp_dirs):
    """Test saving results to JSON."""
    report = {
        'method': 'pearson',
        'n_samples': 10,
        'results': []
    }
    output_path = temp_dirs / 'test_corr.json'
    
    save_results(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded['method'] == 'pearson'
