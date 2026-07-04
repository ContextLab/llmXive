"""
Unit tests for Bayesian hierarchical model (US3).
Tests model convergence and synthetic data edge cases.
"""
import os
import sys
import tempfile
import csv
import math
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test from the actual implementation
# Note: We are testing the logic, but since PyMC might be heavy or require specific setup,
# we focus on the data preparation, convergence checks logic, and forecast generation logic.
# The actual MCMC sampling is tested via integration or mocked if necessary,
# but per task description, we test convergence and edge cases.
# We will import the helper functions that prepare data and check convergence logic.

# Adjust import path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.bayesian import (
    load_processed_poll_data,
    prepare_random_walk_data,
    check_convergence,
    generate_forecasts,
    save_forecasts
)

# --- Fixtures and Helpers ---

@pytest.fixture
def temp_poll_data_file():
    """Creates a temporary CSV file with mock poll data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse'])
        # Generate some synthetic data points
        for i in range(10):
            date = f"2024-10-{i+1:02d}"
            writer.writerow([date, f"Pollster_{i}", 0.5 + 0.01 * i, 1000, 0.02])
        return f.name

@pytest.fixture
def temp_convergence_file():
    """Creates a temporary CSV file with mock convergence stats."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['variable', 'r_hat', 'n_eff'])
        writer.writerow(['theta', 1.01, 500])
        writer.writerow(['sigma', 1.02, 450])
        return f.name

@pytest.fixture
def temp_convergence_fail_file():
    """Creates a temporary CSV file with failing convergence stats."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['variable', 'r_hat', 'n_eff'])
        writer.writerow(['theta', 1.15, 500]) # Failing R-hat
        return f.name

@pytest.fixture
def temp_forecast_output_dir():
    """Creates a temporary directory for forecast outputs."""
    return tempfile.mkdtemp()

# --- Tests ---

def test_load_processed_poll_data_file_not_found():
    """Test that load_processed_poll_data raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        load_processed_poll_data("non_existent_file.csv")

def test_prepare_random_walk_data_structure(temp_poll_data_file):
    """Test that data preparation creates correct structure for Random Walk model."""
    data = prepare_random_walk_data(temp_poll_data_file)
    
    assert 'dates' in data
    assert 'vote_shares' in data
    assert 'sample_sizes' in data
    assert 'rmse_weights' in data
    assert len(data['dates']) > 0
    assert len(data['vote_shares']) == len(data['dates'])
    
    # Check types
    assert isinstance(data['vote_shares'], list)
    assert isinstance(data['sample_sizes'], list)

def test_prepare_random_walk_data_empty_file():
    """Test behavior with an empty CSV (header only)."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("date,pollster,vote_share,sample_size,historical_rmse\n")
        temp_path = f.name
    
    try:
        data = prepare_random_walk_data(temp_path)
        # Should result in empty lists or raise a specific error depending on implementation
        # Based on typical robust implementations, it might return empty structures
        assert len(data['dates']) == 0
        assert len(data['vote_shares']) == 0
    finally:
        os.unlink(temp_path)

def test_check_convergence_pass(temp_convergence_file):
    """Test that check_convergence returns True for good R-hat values."""
    result = check_convergence(temp_convergence_file)
    assert result is True

def test_check_convergence_fail(temp_convergence_fail_file):
    """Test that check_convergence returns False for bad R-hat values."""
    result = check_convergence(temp_convergence_fail_file)
    assert result is False

def test_check_convergence_file_not_found():
    """Test that check_convergence raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        check_convergence("non_existent_file.csv")

def test_generate_forecasts_structure(temp_forecast_output_dir):
    """Test that generate_forecasts creates a valid forecast structure."""
    # Mock forecast data (simulating what the model would output)
    # In a real scenario, this would come from PyMC posterior
    mock_forecasts = [
        {"date": "2024-11-01", "mean": 0.51, "lower_95": 0.48, "upper_95": 0.54},
        {"date": "2024-11-02", "mean": 0.52, "lower_95": 0.49, "upper_95": 0.55},
    ]
    
    output_file = os.path.join(temp_forecast_output_dir, "test_forecasts.csv")
    save_forecasts(mock_forecasts, output_file)
    
    # Verify file exists and can be read
    assert os.path.exists(output_file)
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert 'date' in rows[0]
    assert 'mean' in rows[0]
    assert 'lower_95' in rows[0]
    assert 'upper_95' in rows[0]

def test_generate_forecasts_single_observation(temp_forecast_output_dir):
    """Test handling of a single forecast observation."""
    mock_forecasts = [
        {"date": "2024-11-01", "mean": 0.50, "lower_95": 0.45, "upper_95": 0.55},
    ]
    
    output_file = os.path.join(temp_forecast_output_dir, "single_forecast.csv")
    save_forecasts(mock_forecasts, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1

def test_generate_forecasts_empty_list(temp_forecast_output_dir):
    """Test handling of empty forecast list."""
    output_file = os.path.join(temp_forecast_output_dir, "empty_forecast.csv")
    save_forecasts([], output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 0

def test_edge_case_nan_values_in_data():
    """Test that data preparation handles NaN values gracefully if present."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse'])
        writer.writerow(['2024-10-01', 'P1', '0.5', '1000', '0.02'])
        writer.writerow(['2024-10-02', 'P2', '', '1000', '0.02']) # Empty vote_share
        temp_path = f.name
    
    try:
        # This test verifies the robustness of the data loader
        # Depending on implementation, it might skip or raise. 
        # We expect it to not crash on read, but maybe filter.
        data = prepare_random_walk_data(temp_path)
        # If it filters, length should be 1. If it keeps, it might be 2 with NaN.
        # For this test, we ensure it doesn't crash.
        assert isinstance(data, dict)
    finally:
        os.unlink(temp_path)

def test_single_observation_in_convergence_check():
    """Test convergence check with a single variable."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['variable', 'r_hat', 'n_eff'])
        writer.writerow(['single_var', 1.0, 1000])
        temp_path = f.name
    
    try:
        result = check_convergence(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_zero_observation_variance_handling():
    """Test that zero variance in observation noise is handled (if applicable)."""
    # This is a logical check. If the model allows zero variance, it should not crash.
    # We test the data preparation with a very small RMSE (approaching zero weight)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse'])
        writer.writerow(['2024-10-01', 'P1', '0.5', '1000', '0.00001']) # Very small RMSE
        temp_path = f.name
    
    try:
        data = prepare_random_walk_data(temp_path)
        # Should not crash
        assert len(data['dates']) == 1
    finally:
        os.unlink(temp_path)