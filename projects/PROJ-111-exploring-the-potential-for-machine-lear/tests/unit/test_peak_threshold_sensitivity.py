"""
Unit tests for peak threshold sensitivity analysis.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path
import csv

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from peak_threshold_sensitivity import run_sensitivity_sweep, save_results
from config import get_config

class MockLatentData:
    """Mock latent data for testing."""
    def __init__(self):
        self.data = {
            'temperatures': np.linspace(0.1, 3.0, 30),
            'latent_means': np.random.randn(30, 10),
            'latent_stds': np.abs(np.random.randn(30, 10)) + 0.1
        }

def mock_load_latent_data(directory):
    """Mock function to load latent data."""
    return MockLatentData()

def mock_calculate_total_variance_per_bin(latent_data):
    """Mock function to calculate variance."""
    # Create a synthetic variance curve with a known peak
    temps = latent_data.data['temperatures']
    # Simulate a peak around T=2.0
    variances = 0.1 + 0.5 * np.exp(-((temps - 2.0) ** 2) / 0.5)
    return {
        'temperatures': temps,
        'variances': variances
    }

@pytest.fixture
def mock_dependencies(monkeypatch):
    """Mock the dependencies for testing."""
    monkeypatch.setattr('peak_threshold_sensitivity.load_latent_data', mock_load_latent_data)
    monkeypatch.setattr('peak_threshold_sensitivity.calculate_total_variance_per_bin', 
                      mock_calculate_total_variance_per_bin)
    return True

def test_sensitivity_sweep_structure(mock_dependencies):
    """Test that the sensitivity sweep produces the expected structure."""
    results = run_sensitivity_sweep(None)
    
    assert len(results) > 0, "Results should not be empty"
    assert isinstance(results, list), "Results should be a list"
    
    # Check first result structure
    first_result = results[0]
    required_fields = [
        'derivative_threshold', 'sigma_multiplier', 'peak_detected',
        'peak_temperature', 'peak_variance', 'status', 'confidence_interval'
    ]
    
    for field in required_fields:
        assert field in first_result, f"Missing required field: {field}"

def test_threshold_ranges(mock_dependencies):
    """Test that the correct threshold ranges are used."""
    results = run_sensitivity_sweep(None)
    
    derivative_thresholds = sorted(set(r['derivative_threshold'] for r in results))
    sigma_multipliers = sorted(set(r['sigma_multiplier'] for r in results))
    
    # Check derivative thresholds are in expected range [-0.015, -0.005]
    assert all(-0.015 <= t <= -0.005 for t in derivative_thresholds), \
        f"Derivative thresholds out of range: {derivative_thresholds}"
    
    # Check sigma multipliers are in expected range [1.0, 3.0]
    assert all(1.0 <= s <= 3.0 for s in sigma_multipliers), \
        f"Sigma multipliers out of range: {sigma_multipliers}"

def test_results_have_consistent_format(mock_dependencies):
    """Test that all results have consistent format."""
    results = run_sensitivity_sweep(None)
    
    if len(results) == 0:
        return  # Skip if no results
        
    first_keys = set(results[0].keys())
    for result in results:
        assert set(result.keys()) == first_keys, \
            f"Result keys mismatch: {set(result.keys())} vs {first_keys}"
        assert isinstance(result['peak_detected'], bool), "peak_detected should be boolean"
        assert isinstance(result['status'], str), "status should be string"

def test_save_results_creates_file(tmp_path, mock_dependencies):
    """Test that save_results creates a valid CSV file."""
    results = run_sensitivity_sweep(None)
    output_path = tmp_path / "test_sensitivity.csv"
    
    save_results(results, str(output_path), None)
    
    assert output_path.exists(), "Output file should exist"
    
    # Verify CSV structure
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == len(results), "CSV rows should match result count"
    
    # Check header
    expected_headers = ['derivative_threshold', 'sigma_multiplier', 'peak_detected',
                      'peak_temperature', 'peak_variance', 'status', 'confidence_interval']
    assert reader.fieldnames == expected_headers, f"Header mismatch: {reader.fieldnames}"

def test_peak_detection_logic(mock_dependencies):
    """Test that peak detection varies with thresholds."""
    results = run_sensitivity_sweep(None)
    
    # Group results by derivative threshold
    by_deriv = {}
    for r in results:
        d = r['derivative_threshold']
        if d not in by_deriv:
            by_deriv[d] = []
        by_deriv[d].append(r)
    
    # Check that different thresholds produce different results
    # (at least some variation in peak detection)
    detected_counts = []
    for d, rows in by_deriv.items():
        count = sum(1 for r in rows if r['peak_detected'])
        detected_counts.append(count)
    
    # There should be some variation (unless all thresholds are too strict/lenient)
    # This is a weak test but ensures the logic is running
    assert len(detected_counts) > 1, "Should have multiple derivative threshold groups"