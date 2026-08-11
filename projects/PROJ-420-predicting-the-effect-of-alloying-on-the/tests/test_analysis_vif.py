"""Tests for VIF calculation in analysis module."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis import calculate_vif, save_vif_results

def test_vif_calculation_basic():
    """Test VIF calculation with known data."""
    # Create a simple dataset with some collinearity
    np.random.seed(42)
    n_samples = 100
    
    # Create features with known collinearity
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'feature_4': np.random.randn(n_samples),
        'feature_5': np.random.randn(n_samples)
    })
    
    # Add some collinearity
    X['feature_2'] = X['feature_1'] * 0.9 + np.random.randn(n_samples) * 0.1
    
    feature_columns = ['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5']
    
    vif_results = calculate_vif(X, feature_columns)
    
    # Check that we got results for all features
    assert len(vif_results) == 5
    
    # Check that VIF values are reasonable (positive)
    for result in vif_results:
        assert result['element'] in feature_columns
        assert isinstance(result['vif'], float)
        assert result['vif'] >= 1.0  # VIF is always >= 1
    
    # Check that feature_2 has higher VIF due to collinearity with feature_1
    feature_2_vif = next(r['vif'] for r in vif_results if r['element'] == 'feature_2')
    assert feature_2_vif > 1.5  # Should be higher than 1 due to collinearity

def test_vif_calculation_perfect_collinearity():
    """Test VIF with perfect collinearity (should be very high)."""
    np.random.seed(42)
    n_samples = 50
    
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
    })
    
    # Perfect collinearity
    X['feature_3'] = X['feature_1'] * 2 + X['feature_2'] * 3
    
    feature_columns = ['feature_1', 'feature_2', 'feature_3']
    
    vif_results = calculate_vif(X, feature_columns)
    
    # Check that feature_3 has very high VIF
    feature_3_vif = next(r['vif'] for r in vif_results if r['element'] == 'feature_3')
    assert feature_3_vif > 10.0  # Should be very high due to perfect collinearity

def test_vif_save_results(tmp_path):
    """Test saving VIF results to JSON."""
    np.random.seed(42)
    n_samples = 50
    
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
    })
    
    feature_columns = ['feature_1', 'feature_2']
    vif_results = calculate_vif(X, feature_columns)
    
    output_path = tmp_path / "test_vif_results.json"
    save_vif_results(vif_results, output_path)
    
    # Check that file was created
    assert output_path.exists()
    
    # Check that file contains valid JSON
    with open(output_path, 'r') as f:
        loaded_results = json.load(f)
    
    assert len(loaded_results) == 2
    assert loaded_results[0]['element'] == 'feature_1'
    assert loaded_results[1]['element'] == 'feature_2'
    assert 'vif' in loaded_results[0]
    assert 'vif' in loaded_results[1]

def test_vif_high_collinearity_warning(capsys):
    """Test that warning is logged when VIF > 5.0."""
    np.random.seed(42)
    n_samples = 50
    
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
    })
    
    # Create high collinearity
    X['feature_3'] = X['feature_1'] * 0.95 + X['feature_2'] * 0.95
    
    feature_columns = ['feature_1', 'feature_2', 'feature_3']
    vif_results = calculate_vif(X, feature_columns)
    
    # Check that feature_3 has VIF > 5.0
    feature_3_vif = next(r['vif'] for r in vif_results if r['element'] == 'feature_3')
    assert feature_3_vif > 5.0
