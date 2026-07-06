"""
Unit tests for calibration plotting functionality.
"""
import pytest
import json
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from plots.calibration import (
    aggregate_by_method,
    calculate_binned_metrics,
    load_coverage_data
)

@pytest.fixture
def sample_coverage_data():
    """Generate sample coverage data for testing."""
    return [
        {
            'method_id': 'ols',
            'interval_width': 1.5,
            'covered': True,
            'total_attempts': 1
        },
        {
            'method_id': 'ols',
            'interval_width': 2.0,
            'covered': False,
            'total_attempts': 1
        },
        {
            'method_id': 'ols',
            'interval_width': 1.8,
            'covered': True,
            'total_attempts': 1
        },
        {
            'method_id': 'bootstrap',
            'interval_width': 1.6,
            'covered': True,
            'total_attempts': 1
        },
        {
            'method_id': 'bootstrap',
            'interval_width': 1.9,
            'covered': True,
            'total_attempts': 1
        },
        {
            'method_id': 'bayesian',
            'interval_width': 1.7,
            'covered': False,
            'total_attempts': 1
        },
        {
            'method_id': 'bayesian',
            'interval_width': 2.1,
            'covered': True,
            'total_attempts': 1
        },
        {
            'method_id': 'bayesian',
            'interval_width': 1.4,
            'covered': True,
            'total_attempts': 1
        }
    ]

def test_aggregate_by_method(sample_coverage_data):
    """Test that data is correctly aggregated by method."""
    result = aggregate_by_method(sample_coverage_data)
    
    # Check all expected methods are present
    assert 'OLS' in result
    assert 'Bootstrap' in result
    assert 'Bayesian' in result
    
    # Check OLS aggregation
    assert len(result['OLS']['width']) == 3
    assert len(result['OLS']['coverage']) == 3
    assert result['OLS']['width'] == [1.5, 2.0, 1.8]
    assert result['OLS']['coverage'] == [True, False, True]
    
    # Check Bootstrap aggregation
    assert len(result['Bootstrap']['width']) == 2
    assert result['Bootstrap']['coverage'] == [True, True]
    
    # Check Bayesian aggregation
    assert len(result['Bayesian']['width']) == 3
    assert result['Bayesian']['coverage'] == [False, True, True]

def test_aggregate_by_method_empty_data():
    """Test aggregation with empty data."""
    result = aggregate_by_method([])
    
    assert result['OLS']['width'] == []
    assert result['Bootstrap']['width'] == []
    assert result['Bayesian']['width'] == []

def test_calculate_binned_metrics():
    """Test binning calculation."""
    widths = [1.0, 2.0, 3.0, 4.0, 5.0]
    coverages = [True, True, False, True, False]
    
    bin_centers, mean_covs, counts = calculate_binned_metrics(widths, coverages, n_bins=5)
    
    assert len(bin_centers) == 5
    assert len(mean_covs) == 5
    assert len(counts) == 5
    
    # Check that mean coverage is between 0 and 1
    assert all(0 <= c <= 1 for c in mean_covs)
    
    # Check that counts sum to total samples
    assert sum(counts) == 5

def test_calculate_binned_metrics_empty():
    """Test binning with empty data."""
    bin_centers, mean_covs, counts = calculate_binned_metrics([], [])
    
    assert len(bin_centers) == 0
    assert len(mean_covs) == 0
    assert len(counts) == 0

def test_calculate_binned_mismatched_lengths():
    """Test that mismatched lengths raise an error."""
    with pytest.raises(ValueError):
        calculate_binned_metrics([1.0, 2.0], [True])

def test_load_coverage_data_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_coverage_data()

def test_load_coverage_data_invalid_format(tmp_path):
    """Test loading from a file with invalid format."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not a list or dict")
    
    # Temporarily override the DATA_FILE
    import plots.calibration as cal_module
    original_data_file = cal_module.DATA_FILE
    cal_module.DATA_FILE = invalid_file
    
    try:
        with pytest.raises(ValueError):
            load_coverage_data()
    finally:
        cal_module.DATA_FILE = original_data_file

def test_load_coverage_data_valid_format(tmp_path, sample_coverage_data):
    """Test loading from a valid file."""
    valid_file = tmp_path / "valid.json"
    with open(valid_file, 'w') as f:
        json.dump(sample_coverage_data, f)
    
    # Temporarily override the DATA_FILE
    import plots.calibration as cal_module
    original_data_file = cal_module.DATA_FILE
    cal_module.DATA_FILE = valid_file
    
    try:
        result = load_coverage_data()
        assert len(result) == len(sample_coverage_data)
        assert result[0]['method_id'] == 'ols'
    finally:
        cal_module.DATA_FILE = original_data_file