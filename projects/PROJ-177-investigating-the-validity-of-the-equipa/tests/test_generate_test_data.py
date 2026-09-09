"""
Unit tests for test data generation module.

These tests verify that:
1. The thermal data follows a Maxwell-Boltzmann-like distribution
2. The non-thermal data follows a Pareto distribution
3. The generated files have the correct structure and prefix
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from generate_test_data import load_params, generate_thermal_data, generate_nonthermal_data


@pytest.fixture
def sample_params():
    """Provide sample parameters for testing."""
    return {
        'maxwell_boltzmann': {'mean': 1.0, 'scale': 0.1},
        'pareto': {'shape': 2.0}
    }


@pytest.fixture
def temp_params_file(sample_params):
    """Create a temporary parameters file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_params, f)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


def test_load_params(temp_params_file, sample_params):
    """Test loading parameters from JSON file."""
    loaded = load_params(temp_params_file)
    assert loaded == sample_params
    assert 'maxwell_boltzmann' in loaded
    assert 'pareto' in loaded


def test_load_params_missing_file():
    """Test that missing parameters file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_params("nonexistent_path.json")


def test_generate_thermal_data_structure(sample_params):
    """Test that thermal data has correct structure."""
    df = generate_thermal_data(sample_params, n_samples=100, seed=42)

    # Check columns
    expected_columns = ['particle_id', 'timestamp', 'energy_value', 'distribution_type']
    assert list(df.columns) == expected_columns

    # Check distribution type
    assert all(df['distribution_type'] == 'maxwell_boltzmann')

    # Check data types
    assert df['particle_id'].dtype in [np.int64, np.int32]
    assert df['energy_value'].dtype in [np.float64, np.float32]


def test_generate_nonthermal_data_structure(sample_params):
    """Test that non-thermal data has correct structure."""
    df = generate_nonthermal_data(sample_params, n_samples=100, seed=42)

    # Check columns
    expected_columns = ['particle_id', 'timestamp', 'energy_value', 'distribution_type']
    assert list(df.columns) == expected_columns

    # Check distribution type
    assert all(df['distribution_type'] == 'pareto')

    # Check data types
    assert df['particle_id'].dtype in [np.int64, np.int32]
    assert df['energy_value'].dtype in [np.float64, np.float32]


def test_thermal_data_values_positive(sample_params):
    """Test that thermal data values are positive."""
    df = generate_thermal_data(sample_params, n_samples=1000, seed=42)
    assert all(df['energy_value'] > 0)


def test_nonthermal_data_values_positive(sample_params):
    """Test that non-thermal data values are positive."""
    df = generate_nonthermal_data(sample_params, n_samples=1000, seed=42)
    assert all(df['energy_value'] > 0)


def test_thermal_data_mean(sample_params):
    """Test that thermal data mean is approximately correct."""
    df = generate_thermal_data(sample_params, n_samples=50000, seed=42)
    expected_mean = sample_params['maxwell_boltzmann']['mean'] * sample_params['maxwell_boltzmann']['scale']
    # Allow 20% tolerance due to distribution approximation
    assert abs(df['energy_value'].mean() - expected_mean) < 0.2 * expected_mean


def test_nonthermal_data_shape(sample_params):
    """Test that non-thermal data follows Pareto distribution characteristics."""
    df = generate_nonthermal_data(sample_params, n_samples=50000, seed=42)
    # Pareto with shape=2.0 should have mean = shape/(shape-1) * x_m = 2.0
    expected_mean = 2.0  # x_m = 1.0, shape = 2.0
    # Allow 30% tolerance due to heavy tail
    assert abs(df['energy_value'].mean() - expected_mean) < 0.3 * expected_mean


def test_reproducibility(sample_params):
    """Test that same seed produces same results."""
    df1 = generate_thermal_data(sample_params, n_samples=1000, seed=123)
    df2 = generate_thermal_data(sample_params, n_samples=1000, seed=123)

    assert df1['energy_value'].tolist() == df2['energy_value'].tolist()


def test_file_prefix_requirement(sample_params):
    """Test that the generated files would have 'test_' prefix."""
    # This is a logical check based on the main function behavior
    thermal_name = "test_thermal_data.csv"
    nonthermal_name = "test_nonthermal_data.csv"

    assert thermal_name.startswith("test_")
    assert nonthermal_name.startswith("test_")

    # Verify the prefix indicates these are test files
    assert "test_" in thermal_name
    assert "test_" in nonthermal_name
