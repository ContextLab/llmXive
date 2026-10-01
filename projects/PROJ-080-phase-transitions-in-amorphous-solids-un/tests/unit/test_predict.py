"""
Unit tests for sensitivity sweep logic in code/predict.py.
"""
import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
from predict import sweep_threshold, define_time_to_failure, create_holdout_split

# Mock data fixtures
@pytest.fixture
def mock_d2_min_data():
    """Generate deterministic mock D2_min values for testing."""
    np.random.seed(42)
    n_samples = 100
    # Simulate brittle vs ductile distributions
    # Brittle: higher D2_min values (more shear localization)
    # Ductile: lower D2_min values (more homogeneous deformation)
    brittle_values = np.random.normal(loc=0.15, scale=0.03, size=50)
    ductile_values = np.random.normal(loc=0.08, scale=0.02, size=50)
    
    # Create dataframe
    df = pd.DataFrame({
        'd2_min': np.concatenate([brittle_values, ductile_values]),
        'label': ['brittle'] * 50 + ['ductile'] * 50,
        'time_to_failure': np.concatenate([
            np.random.normal(loc=0.95, scale=0.02, size=50),
            np.random.normal(loc=0.85, scale=0.03, size=50)
        ])
    })
    return df

@pytest.fixture
def mock_threshold():
    """Return a base threshold for sensitivity sweep."""
    return 0.12

@pytest.fixture
def mock_holdout_split(mock_d2_min_data):
    """Create a mock holdout split."""
    indices = list(range(len(mock_d2_min_data)))
    np.random.seed(42)
    np.random.shuffle(indices)
    split_point = int(len(indices) * 0.8)
    train_indices = indices[:split_point]
    val_indices = indices[split_point:]
    return {
        'train_indices': train_indices,
        'val_indices': val_indices
    }

def test_sweep_threshold_range(mock_d2_min_data, mock_threshold):
    """Test that sweep_threshold generates the correct number of threshold values."""
    thresholds = sweep_threshold(mock_d2_min_data, mock_threshold)
    
    # Should generate 3 thresholds: [threshold - 0.05, threshold, threshold + 0.05]
    assert len(thresholds) == 3
    assert thresholds[0] == pytest.approx(mock_threshold - 0.05)
    assert thresholds[1] == pytest.approx(mock_threshold)
    assert thresholds[2] == pytest.approx(mock_threshold + 0.05)

def test_sweep_threshold_output_structure(mock_d2_min_data, mock_threshold):
    """Test that sweep_threshold returns the correct output structure."""
    results = sweep_threshold(mock_d2_min_data, mock_threshold)
    
    # Should be a list of dictionaries with specific keys
    assert isinstance(results, list)
    assert len(results) == 3
    
    for result in results:
        assert 'threshold' in result
        assert 'tp' in result
        assert 'tn' in result
        assert 'fp' in result
        assert 'fn' in result
        assert 'fpr' in result
        assert 'fnr' in result
        assert 'f1' in result

def test_sweep_threshold_metrics_logic(mock_d2_min_data, mock_threshold):
    """Test that metrics are calculated correctly (no NaN/Inf)."""
    results = sweep_threshold(mock_d2_min_data, mock_threshold)
    
    for result in results:
        # Check that all metrics are finite numbers
        assert np.isfinite(result['f1'])
        assert np.isfinite(result['fpr'])
        assert np.isfinite(result['fnr'])
        assert np.isfinite(result['tp'])
        assert np.isfinite(result['tn'])
        assert np.isfinite(result['fp'])
        assert np.isfinite(result['fn'])
        
        # Check that FPR and FNR are in [0, 1]
        assert 0 <= result['fpr'] <= 1
        assert 0 <= result['fnr'] <= 1
        assert 0 <= result['f1'] <= 1

def test_sweep_threshold_consistency(mock_d2_min_data, mock_threshold):
    """Test that the same input produces consistent results."""
    results1 = sweep_threshold(mock_d2_min_data, mock_threshold)
    results2 = sweep_threshold(mock_d2_min_data, mock_threshold)
    
    # Results should be identical
    for r1, r2 in zip(results1, results2):
        assert r1['f1'] == pytest.approx(r2['f1'])
        assert r1['fpr'] == pytest.approx(r2['fpr'])
        assert r1['fnr'] == pytest.approx(r2['fnr'])

def test_sweep_threshold_edge_cases(mock_d2_min_data):
    """Test sensitivity sweep with extreme threshold values."""
    # Test with very low threshold (should classify most as brittle)
    low_threshold = 0.01
    results_low = sweep_threshold(mock_d2_min_data, low_threshold)
    
    # Test with very high threshold (should classify most as ductile)
    high_threshold = 0.30
    results_high = sweep_threshold(mock_d2_min_data, high_threshold)
    
    # Both should produce valid results
    assert len(results_low) == 3
    assert len(results_high) == 3
    
    for result in results_low + results_high:
        assert all(np.isfinite(v) for k, v in result.items() if k != 'threshold')

def test_define_time_to_failure(mock_d2_min_data):
    """Test that time_to_failure is correctly defined."""
    ttf = define_time_to_failure(mock_d2_min_data)
    
    # Should be a numpy array
    assert isinstance(ttf, np.ndarray)
    assert len(ttf) == len(mock_d2_min_data)
    
    # Should contain finite values
    assert np.all(np.isfinite(ttf))

def test_create_holdout_split(mock_d2_min_data):
    """Test that holdout split creates valid indices."""
    split = create_holdout_split(mock_d2_min_data, seed=42)
    
    # Should return a dictionary with train and val indices
    assert 'train_indices' in split
    assert 'val_indices' in split
    
    # All indices should be unique and within range
    all_indices = split['train_indices'] + split['val_indices']
    assert len(all_indices) == len(mock_d2_min_data)
    assert len(set(all_indices)) == len(all_indices)
    assert all(0 <= i < len(mock_d2_min_data) for i in all_indices)

def test_sweep_threshold_with_validation_split(mock_d2_min_data, mock_threshold, mock_holdout_split):
    """Test sensitivity sweep using only validation data."""
    val_data = mock_d2_min_data.iloc[mock_holdout_split['val_indices']]
    results = sweep_threshold(val_data, mock_threshold)
    
    # Should produce valid metrics for validation set
    assert len(results) == 3
    for result in results:
        assert result['f1'] >= 0
        assert result['f1'] <= 1
        assert np.isfinite(result['f1'])