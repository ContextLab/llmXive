"""
Unit tests for fit_utils.py
"""
import json
import os
import tempfile
import numpy as np
import pytest

from analysis.fit_utils import (
    load_mc_results,
    aggregate_by_theta,
    sigmoid_function,
    fit_critical_threshold,
    analyze_threshold_identification
)


@pytest.fixture
def sample_mc_csv(tmp_path):
    """Create a sample Monte Carlo results CSV file."""
    csv_path = tmp_path / "mc_results.csv"
    content = """run_id,N,theta,seed,outlier_count,max_eigenvalue
    1,1000,1.5,42,0,1.98
    2,1000,1.5,43,0,1.97
    3,1000,2.0,44,0,2.01
    4,1000,2.0,45,1,2.15
    5,1000,2.5,46,1,2.30
    6,1000,2.5,47,1,2.28
    7,1000,3.0,48,1,2.45
    8,1000,3.0,49,1,2.42
    """
    csv_path.write_text(content)
    return str(csv_path)


@pytest.fixture
def sample_mc_csv_partial(tmp_path):
    """Create a sample CSV with only one theta value (insufficient for fitting)."""
    csv_path = tmp_path / "mc_results_partial.csv"
    content = """run_id,N,theta,seed,outlier_count,max_eigenvalue
    1,1000,2.0,42,0,1.98
    2,1000,2.0,43,1,2.10
    """
    csv_path.write_text(content)
    return str(csv_path)


def test_load_mc_results(sample_mc_csv):
    """Test loading Monte Carlo results from CSV."""
    data = load_mc_results(sample_mc_csv)
    assert data.shape == (8, 3), f"Expected shape (8, 3), got {data.shape}"
    assert data[0, 0] == 1.5, "First theta value should be 1.5"
    assert data[1, 1] == 0, "First outlier flag should be 0"
    assert data[4, 1] == 1, "Fifth outlier flag should be 1"


def test_load_mc_results_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_mc_results("nonexistent_file.csv")


def test_aggregate_by_theta(sample_mc_csv):
    """Test aggregation of results by theta value."""
    data = load_mc_results(sample_mc_csv)
    thetas, probs, counts = aggregate_by_theta(data)
    
    assert len(thetas) == 4, f"Expected 4 unique thetas, got {len(thetas)}"
    assert np.allclose(thetas, [1.5, 2.0, 2.5, 3.0])
    
    # Check probabilities: 0/2, 1/2, 2/2, 2/2
    expected_probs = [0.0, 0.5, 1.0, 1.0]
    assert np.allclose(probs, expected_probs), f"Expected {expected_probs}, got {probs.tolist()}"
    
    assert np.all(counts == 2), "All counts should be 2"


def test_sigmoid_function():
    """Test the sigmoid function implementation."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    a, b = 10.0, 2.0
    
    result = sigmoid_function(x, a, b)
    
    # At x = b, sigmoid should be 0.5
    assert np.isclose(result[1], 0.5, atol=1e-6), "Sigmoid at center should be 0.5"
    
    # For x << b, sigmoid should be near 0
    assert result[0] < 0.1, "Sigmoid should be near 0 for x << b"
    
    # For x >> b, sigmoid should be near 1
    assert result[-1] > 0.9, "Sigmoid should be near 1 for x >> b"


def test_fit_critical_threshold_success(sample_mc_csv):
    """Test successful fitting of critical threshold."""
    data = load_mc_results(sample_mc_csv)
    thetas, probs, counts = aggregate_by_theta(data)
    
    result = fit_critical_threshold(thetas, probs, counts)
    
    assert result['success'], f"Fitting failed: {result['message']}"
    assert result['theta_c'] is not None
    assert result['steepness'] is not None
    assert 1.5 < result['theta_c'] < 2.5, f"theta_c {result['theta_c']} out of expected range"


def test_fit_critical_threshold_insufficient_data(sample_mc_csv_partial):
    """Test fitting with insufficient data points."""
    data = load_mc_results(sample_mc_csv_partial)
    thetas, probs, counts = aggregate_by_theta(data)
    
    result = fit_critical_threshold(thetas, probs, counts)
    
    assert not result['success']
    assert 'Insufficient data' in result['message']


def test_analyze_threshold_identification(sample_mc_csv, tmp_path):
    """Test the full analysis pipeline."""
    output_path = tmp_path / "threshold_raw.json"
    
    result = analyze_threshold_identification(sample_mc_csv, str(output_path))
    
    assert output_path.exists(), "Output file was not created"
    
    with open(output_path) as f:
        loaded = json.load(f)
    
    assert 'metadata' in loaded
    assert 'aggregated_data' in loaded
    assert 'summary_statistics' in loaded
    assert loaded['metadata']['unique_theta_values'] == 4
    assert len(loaded['aggregated_data']['thetas']) == 4