"""
Unit tests for the convergence checker module.

Tests the convergence detection logic for Green-Kubo simulations.
"""

import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# Import the module under test
from simulation.convergence_checker import (
    calculate_hcacf_relative_change,
    check_convergence,
    update_thermal_sample_metadata,
    process_convergence_for_sample,
    DEFAULT_CONVERGENCE_THRESHOLD,
    DEFAULT_FINAL_SEGMENT_FRACTION
)

@pytest.fixture
def mock_sample_data():
    """Create a mock ThermalSample dictionary."""
    return {
        "sample_id": "test_sample_001",
        "conductivity": 1.5,
        "metadata": {
            "source": "test",
            "timestamp": "2024-01-01"
        },
        "hcacf_data": np.array([1.0, 0.8, 0.6, 0.5, 0.4, 0.35, 0.32, 0.30, 0.29, 0.285])
    }

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "output"

def test_calculate_hcacf_relative_change_converged():
    """Test convergence detection with stable HCACF data."""
    # Create data where the final segment is very stable
    hcacf_data = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.39, 0.385, 0.380, 0.378, 0.377])
    
    relative_change, mean_first, mean_second = calculate_hcacf_relative_change(
        hcacf_data, segment_fraction=0.25
    )
    
    # The relative change should be small (< 1%)
    assert relative_change < 0.01
    assert mean_first > 0
    assert mean_second > 0
    assert abs(mean_first - mean_second) / mean_first < 0.01

def test_calculate_hcacf_relative_change_not_converged():
    """Test convergence detection with unstable HCACF data."""
    # Create data where the final segment has significant drift
    hcacf_data = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01])
    
    relative_change, mean_first, mean_second = calculate_hcacf_relative_change(
        hcacf_data, segment_fraction=0.25
    )
    
    # The relative change should be large (> 1%)
    assert relative_change > 0.01

def test_calculate_hcacf_relative_change_short_data():
    """Test convergence detection with very short data."""
    hcacf_data = np.array([1.0, 0.8, 0.6])
    
    relative_change, mean_first, mean_second = calculate_hcacf_relative_change(hcac_data)
    
    # Should return infinity for very short data
    assert relative_change == float('inf')

def test_check_convergence_converged():
    """Test the full convergence check with converged data."""
    # Stable data
    hcacf_data = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.39, 0.385, 0.380, 0.378, 0.377])
    
    result = check_convergence(hcac_data, threshold=0.01)
    
    assert result["converged"] is True
    assert result["relative_change"] < 0.01
    assert result["threshold"] == 0.01
    assert "mean_first_half" in result
    assert "mean_second_half" in result

def test_check_convergence_not_converged():
    """Test the full convergence check with non-converged data."""
    # Unstable data
    hcacf_data = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01])
    
    result = check_convergence(hcac_data, threshold=0.01)
    
    assert result["converged"] is False
    assert result["relative_change"] > 0.01

def test_update_thermal_sample_metadata():
    """Test updating ThermalSample metadata with convergence results."""
    sample = {
        "sample_id": "test_001",
        "conductivity": 1.5,
        "metadata": {"original": "data"}
    }
    
    convergence_result = {
        "converged": True,
        "relative_change": 0.005,
        "threshold": 0.01,
        "mean_first_half": 0.38,
        "mean_second_half": 0.378,
        "segment_fraction": 0.2,
        "total_points": 100,
        "segment_points": 20
    }
    
    updated = update_thermal_sample_metadata(sample, convergence_result)
    
    assert "converged" in updated
    assert updated["converged"] is True
    assert "metadata" in updated
    assert "convergence" in updated["metadata"]
    assert updated["metadata"]["convergence"]["converged"] is True
    assert updated["metadata"]["convergence"]["relative_change"] == 0.005
    assert updated["metadata"]["convergence"]["details"]["mean_first_half"] == 0.38

def test_process_convergence_for_sample(mock_sample_data, temp_output_dir):
    """Test processing a single sample file for convergence."""
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False) as f:
        pickle.dump(mock_sample_data, f)
        input_path = Path(f.name)
    
    try:
        # Process the sample
        result = process_convergence_for_sample(input_path, temp_output_dir)
        
        assert result["status"] == "completed"
        assert "converged" in result
        assert result["output_path"] == str(temp_output_dir / input_path.name)
        
        # Verify the output file was created and contains updated data
        output_path = Path(result["output_path"])
        assert output_path.exists()
        
        with open(output_path, 'rb') as f:
            output_data = pickle.load(f)
        
        assert "converged" in output_data
        assert "metadata" in output_data
        assert "convergence" in output_data["metadata"]
        
    finally:
        input_path.unlink()

def test_process_convergence_for_sample_no_hcacf(temp_output_dir):
    """Test processing a sample without HCACF data."""
    sample_data = {
        "sample_id": "test_no_hcacf",
        "conductivity": 1.5,
        "metadata": {}
    }
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False) as f:
        pickle.dump(sample_data, f)
        input_path = Path(f.name)
    
    try:
        result = process_convergence_for_sample(input_path, temp_output_dir)
        
        assert result["status"] == "skipped"
        assert result["reason"] == "No HCACF data found"
        
    finally:
        input_path.unlink()

def test_check_convergence_custom_threshold():
    """Test convergence check with custom threshold."""
    hcacf_data = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.39, 0.385, 0.380, 0.378, 0.377])
    
    # With a very strict threshold, it should not converge
    result_strict = check_convergence(hcac_data, threshold=0.001)
    assert result_strict["converged"] is False
    
    # With a loose threshold, it should converge
    result_loose = check_convergence(hcac_data, threshold=0.1)
    assert result_loose["converged"] is True