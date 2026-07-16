"""
Unit tests for power-law model fitting (T016) and convergence handling (T033, T038).
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Import the module under test
from analysis.fitting import (
    fit_power_law_model,
    run_fitting_for_subject,
    generate_fitting_report,
    load_avalanche_sizes_from_store
)

@pytest.fixture
def sample_avalanche_sizes():
    """Generate synthetic data that approximates a power-law distribution."""
    # Using a Pareto distribution as a proxy for power-law
    alpha_true = 2.5
    size_min = 1.0
    # Generate 1000 samples
    data = np.random.pareto(alpha_true, 1000) + size_min
    # Round to integers to simulate discrete avalanche sizes
    return list(np.round(data).astype(int))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data layout."""
    avalanche_dir = tmp_path / "processed" / "avalanches"
    avalanche_dir.mkdir(parents=True)
    return tmp_path

def test_fit_power_law_model_success(sample_avalanche_sizes):
    """Test that fitting a power-law model returns expected keys."""
    result = fit_power_law_model(sample_avalanche_sizes)
    
    assert 'fit_successful' in result
    assert result['fit_successful'] is True
    assert 'alpha' in result
    assert 'xmin' in result
    assert 'comparison' in result
    assert 'vs_exponential' in result['comparison']
    assert 'vs_lognormal' in result['comparison']
    assert 'best_model' in result
    assert result['alpha'] > 0.0
    assert result['xmin'] > 0.0

def test_fit_power_law_model_insufficient_data():
    """Test fitting with too few data points."""
    result = fit_power_law_model([1, 2])
    # Should fail gracefully, not crash
    assert 'error' in result or not result.get('fit_successful', False)

def test_fit_power_law_model_empty_input():
    """Test fitting with empty input."""
    result = fit_power_law_model([])
    assert 'error' in result or not result.get('fit_successful', False)

def test_run_fitting_for_subject(sample_avalanche_sizes):
    """Test the subject-level runner."""
    result = run_fitting_for_subject("sub-001", sample_avalanche_sizes)
    
    assert result['subject_id'] == "sub-001"
    assert result['n_avalanches'] == len(sample_avalanche_sizes)
    assert result['fit_successful'] is True
    assert 'alpha' in result

def test_generate_fitting_report(tmp_path, sample_avalanche_sizes):
    """Test report generation."""
    results = [
        run_fitting_for_subject("sub-001", sample_avalanche_sizes),
        run_fitting_for_subject("sub-002", sample_avalanche_sizes)
    ]
    
    output_path = tmp_path / "fitting_report.csv"
    generate_fitting_report(results, output_path)
    
    assert output_path.exists()
    
    # Verify CSV content
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert 'subject_id' in df.columns
    assert 'alpha' in df.columns
    assert 'best_model' in df.columns
    assert df['subject_id'].iloc[0] == "sub-001"

def test_load_avalanche_sizes_from_store(temp_data_dir):
    """Test loading data from the simulated store."""
    # Create a mock CSV file
    csv_path = temp_data_dir / "processed" / "avalanches" / "sub-001_avalanches.csv"
    df = pd.DataFrame({'size': [1, 2, 3, 4, 5, 10, 20]})
    df.to_csv(csv_path, index=False)
    
    loaded = load_avalanche_sizes_from_store(temp_data_dir)
    
    assert 'sub-001' in loaded
    assert loaded['sub-001'] == [1, 2, 3, 4, 5, 10, 20]

def test_load_avalanche_sizes_from_store_missing_file(temp_data_dir):
    """Test loading when no files exist."""
    loaded = load_avalanche_sizes_from_store(temp_data_dir)
    assert loaded == {}

def test_fit_power_law_convergence_failure_logs_error(caplog, sample_avalanche_sizes):
    """
    Test T033/T038: Verify that when powerlaw convergence fails, 
    the function logs a specific error code and returns fit_successful=False.
    """
    # Mock the powerlaw.Fit to raise an exception or return a failure state
    # We simulate a scenario where the fit fails due to convergence issues
    with patch('powerlaw.Fit') as mock_fit_class:
        # Configure the mock to raise a generic exception simulating convergence failure
        mock_fit_instance = MagicMock()
        mock_fit_instance.power_law.alpha = 2.5
        # Simulate a failure in the comparison or fitting process
        mock_fit_class.side_effect = Exception("Convergence failed: Optimization did not converge")
        
        with caplog.at_level(logging.ERROR):
            result = fit_power_law_model(sample_avalanche_sizes)
            
            # Verify the result indicates failure
            assert result.get('fit_successful') is False
            assert 'error' in result
            
            # Verify the specific error code or message is logged
            # The implementation should log a specific error code for this case
            assert any("CONVERGENCE_FAIL" in record.message for record in caplog.records) or \
                   any("Convergence failed" in record.message for record in caplog.records)

def test_run_fitting_for_subject_handles_convergence_failure(caplog):
    """
    Test T033/T038: Verify that run_fitting_for_subject handles convergence failure
    by excluding the participant (fit_successful=False) and logging the error.
    """
    # Prepare a dataset that might cause issues or mock the failure
    small_data = [1, 2, 3] # Very small dataset often causes fitting issues
    
    with patch('powerlaw.Fit') as mock_fit_class:
        mock_fit_class.side_effect = Exception("Convergence failed")
        
        with caplog.at_level(logging.ERROR):
            result = run_fitting_for_subject("sub-fail", small_data)
            
            assert result['subject_id'] == "sub-fail"
            assert result['fit_successful'] is False
            assert result.get('alpha') is None
            
            # Ensure the error was logged so it can be excluded from correlation analysis
            assert any("CONVERGENCE_FAIL" in record.message for record in caplog.records) or \
                   any("Convergence failed" in record.message for record in caplog.records)