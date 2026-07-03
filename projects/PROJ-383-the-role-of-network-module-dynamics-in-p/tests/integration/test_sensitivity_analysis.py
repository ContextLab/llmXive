import pytest
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sensitivity_analysis import (
    run_sensitivity_analysis,
    calculate_correlation_with_behavior,
    compute_flexibility_for_window_length
)

@pytest.fixture
def mock_data(tmp_path):
    """Create mock data for testing."""
    # Create necessary directories
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create mock scrubbed timeseries
    mock_timeseries = pd.DataFrame({
        'subject_id': ['sub-01', 'sub-01', 'sub-02', 'sub-02'],
        'time_series': [
            np.random.rand(100, 200),  # 100 time points, 200 regions
            np.random.rand(100, 200),
            np.random.rand(100, 200),
            np.random.rand(100, 200)
        ]
    })
    mock_timeseries.to_parquet(processed_dir / "scrubbed_timeseries.parquet")
    
    # Create mock consolidated data
    mock_consolidated = pd.DataFrame({
        'subject_id': ['sub-01', 'sub-02'],
        'nback_accuracy': [0.85, 0.72],
        'mean_fd': [0.15, 0.18]
    })
    mock_consolidated.to_parquet(processed_dir / "consolidated_data.parquet")
    
    return tmp_path

@pytest.fixture
def mock_flexibility_function():
    """Mock the flexibility calculation to return deterministic values."""
    with patch('analysis.sensitivity_analysis.compute_flexibility_metric') as mock_func:
        # Return a simple deterministic value based on window length
        def mock_calc(time_series, window_length, step_size):
            # Return a value that varies slightly with window length
            return 0.5 + (window_length / 1000)
        
        mock_func.side_effect = mock_calc
        yield mock_func

def test_sensitivity_analysis_runs(mock_data, mock_flexibility_function, tmp_path):
    """Test that sensitivity analysis runs without crashing."""
    # Patch paths to use temp directory
    with patch('analysis.sensitivity_analysis.DATA_PATH', mock_data / "data" / "processed"), \
         patch('analysis.sensitivity_analysis.OUTPUT_PATH', tmp_path / "sensitivity_analysis.json"):
        
        results = run_sensitivity_analysis()
        
        # Check that results were generated
        assert results is not None
        assert "window_lengths" in results
        assert "results" in results
        assert "stability_check" in results
        
        # Check that output file was created
        output_file = tmp_path / "sensitivity_analysis.json"
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            saved_results = json.load(f)
        
        assert saved_results == results

def test_correlation_calculation(mock_data):
    """Test that correlation calculation works correctly."""
    # Create mock flexibility scores
    flexibility_scores = {
        'sub-01': 0.65,
        'sub-02': 0.72,
        'sub-03': 0.58
    }
    
    # Create mock behavioral data
    behavioral_df = pd.DataFrame({
        'subject_id': ['sub-01', 'sub-02', 'sub-03'],
        'nback_accuracy': [0.85, 0.72, 0.90],
        'mean_fd': [0.15, 0.18, 0.12]
    })
    
    correlation = calculate_correlation_with_behavior(flexibility_scores, behavioral_df)
    
    # Check that correlation is a float
    assert isinstance(correlation, float)
    # Check that correlation is within valid range [-1, 1]
    assert -1.0 <= correlation <= 1.0

def test_sensitivity_threshold_check(mock_data, mock_flexibility_function, tmp_path):
    """Test that stability threshold is correctly evaluated."""
    # Mock flexibility to create specific correlation patterns
    with patch('analysis.sensitivity_analysis.compute_flexibility_metric') as mock_func:
        # Create a pattern where correlations are very close
        def mock_calc(time_series, window_length, step_size):
            # All return similar values to ensure small differences
            return 0.5 + (window_length % 10) / 10000
        
        mock_func.side_effect = mock_calc
        
        with patch('analysis.sensitivity_analysis.DATA_PATH', mock_data / "data" / "processed"), \
             patch('analysis.sensitivity_analysis.OUTPUT_PATH', tmp_path / "sensitivity_analysis.json"):
            
            results = run_sensitivity_analysis()
            
            # Check stability check results
            stability = results.get("stability_check", {})
            assert "passed" in stability
            assert "max_absolute_difference" in stability
            
            # With our mock, differences should be very small
            assert stability["max_absolute_difference"] < 0.05
            assert stability["passed"] is True

def test_empty_flexibility_scores(mock_data, tmp_path):
    """Test handling of empty flexibility scores."""
    with patch('analysis.sensitivity_analysis.compute_flexibility_for_window_length') as mock_func:
        mock_func.return_value = {}  # Return empty dict
        
        with patch('analysis.sensitivity_analysis.DATA_PATH', mock_data / "data" / "processed"), \
             patch('analysis.sensitivity_analysis.OUTPUT_PATH', tmp_path / "sensitivity_analysis.json"):
            
            results = run_sensitivity_analysis()
            
            # Should still complete, but with empty results for that window
            assert results is not None
            # Check that the window length is in the results but with no data
            for wl in results["window_lengths"]:
                if str(wl) in results["results"]:
                    assert "correlation" in results["results"][str(wl)]

def test_nan_handling_in_correlation():
    """Test that NaN values are handled correctly in correlation calculation."""
    # Create mock data with some NaN values
    flexibility_scores = {
        'sub-01': 0.65,
        'sub-02': np.nan,  # NaN value
        'sub-03': 0.58
    }
    
    behavioral_df = pd.DataFrame({
        'subject_id': ['sub-01', 'sub-02', 'sub-03'],
        'nback_accuracy': [0.85, 0.72, 0.90],
        'mean_fd': [0.15, 0.18, 0.12]
    })
    
    # Should not crash and should return a valid correlation
    correlation = calculate_correlation_with_behavior(flexibility_scores, behavioral_df)
    
    assert isinstance(correlation, float)
    assert not np.isnan(correlation)
    assert -1.0 <= correlation <= 1.0
