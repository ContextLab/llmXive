"""
Unit tests for T018: run_simulation.py

Tests verify:
- Seed reproducibility
- Correct column structure in output
- Expected data types
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.run_simulation import (
    run_single_test_iteration,
    run_monte_carlo_simulation,
    load_sensitivity_data
)
from utils.config import get_seed

@pytest.fixture
def sample_sensitivity_data():
    """Create sample sensitivity data for testing."""
    data = {
        'dataset': ['wine', 'wine', 'har'],
        'contamination_rate': [0.0, 0.1, 0.0],
        'threshold': [1.0, 2.0, 1.5],
        'false_positive_rate': [0.05, 0.12, 0.06],
        'variation_in_fpr': [0.01, 0.03, 0.02]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_sensitivity_file(tmp_path, sample_sensitivity_data):
    """Create a temporary sensitivity.csv file."""
    file_path = tmp_path / "sensitivity.csv"
    sample_sensitivity_data.to_csv(file_path, index=False)
    return file_path

def test_run_single_test_iteration_clean_data():
    """Test single iteration with clean data (null hypothesis)."""
    # Create clean dataset
    dataset = pd.DataFrame(np.random.randn(100, 5))
    
    error, power = run_single_test_iteration(
        dataset=dataset,
        contamination_rate=0.0,
        magnitude=1.0,
        seed=42
    )
    
    # For clean data, we expect some Type I errors (around 5%)
    # but power should be 0 since null hypothesis is true
    assert isinstance(error, (int, float))
    assert isinstance(power, (int, float))
    assert 0 <= error <= 1
    assert power == 0.0  # No power calculation for null hypothesis

def test_run_single_test_iteration_contaminated_data():
    """Test single iteration with contaminated data (alternative hypothesis)."""
    dataset = pd.DataFrame(np.random.randn(100, 5))
    
    error, power = run_single_test_iteration(
        dataset=dataset,
        contamination_rate=0.1,
        magnitude=2.0,
        seed=42
    )
    
    # For contaminated data, we measure power
    # error should be 0 (not applicable)
    assert isinstance(error, (int, float))
    assert isinstance(power, (int, float))
    assert error == 0.0  # Not applicable for alternative hypothesis
    assert 0 <= power <= 1

def test_seed_reproducibility():
    """Test that same seed produces same results."""
    dataset = pd.DataFrame(np.random.randn(100, 5))
    
    error1, power1 = run_single_test_iteration(
        dataset=dataset,
        contamination_rate=0.0,
        magnitude=1.0,
        seed=42
    )
    
    error2, power2 = run_single_test_iteration(
        dataset=dataset,
        contamination_rate=0.0,
        magnitude=1.0,
        seed=42
    )
    
    assert error1 == error2
    assert power1 == power2

@patch('code.data.run_simulation.load_sensitivity_data')
@patch('code.data.run_simulation.load_contaminated_datasets')
def test_run_monte_carlo_simulation_structure(mock_load_datasets, mock_load_sensitivity, temp_sensitivity_file):
    """Test that simulation returns expected structure."""
    # Mock dependencies
    mock_load_sensitivity.return_value = pd.read_csv(temp_sensitivity_file)
    mock_load_datasets.return_value = {
        'wine_rate_0.0_mag_1.0': pd.DataFrame(np.random.randn(100, 5)),
        'wine_rate_0.1_mag_2.0': pd.DataFrame(np.random.randn(100, 5))
    }
    
    # Run simulation with reduced iterations for speed
    with patch('code.data.run_simulation.NUM_ITERATIONS', 10):
        result = run_monte_carlo_simulation(
            dataset_name='wine',
            contamination_rate=0.0,
            magnitude=1.0,
            num_iterations=10
        )
    
    # Verify result structure
    assert isinstance(result, dict)
    assert 'dataset' in result
    assert 'rate' in result
    assert 'magnitude' in result
    assert 'error_rate' in result
    assert 'power' in result
    assert 'num_iterations' in result
    
    # Verify data types
    assert result['dataset'] == 'wine'
    assert result['rate'] == 0.0
    assert result['magnitude'] == 1.0
    assert isinstance(result['error_rate'], float)
    assert isinstance(result['power'], float)
    assert result['num_iterations'] == 10

def test_load_sensitivity_data_file_not_found():
    """Test error handling when sensitivity file is missing."""
    with pytest.raises(FileNotFoundError, match="Sensitivity analysis file not found"):
        # This will fail because the file doesn't exist in the expected location
        load_sensitivity_data()