"""
Pytest configuration and base test fixtures for the Power Drift Detection project.

This file provides:
- Custom markers for test categorization
- Fixtures for temporary directories
- Fixtures for mock data structures (for unit tests only)
- Fixtures for the real data path (integration tests)
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the project root to sys.path to ensure local imports work
# This assumes tests/ is at the root level relative to code/
project_root = Path(__file__).parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# ----------------------------------------------------------------------
# Custom Markers
# ----------------------------------------------------------------------

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test artifacts.
    Ensures clean state for each test and cleanup afterwards.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def project_root_path():
    """Return the path to the project root."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_derived_path(project_root_path):
    """Return the path to the derived data directory."""
    return project_root_path / "data" / "derived"

@pytest.fixture
def data_raw_path(project_root_path):
    """Return the path to the raw data directory."""
    return project_root_path / "data" / "raw"

@pytest.fixture
def results_path(project_root_path):
    """Return the path to the results directory."""
    return project_root_path / "results"

@pytest.fixture
def mock_sample_data_dict():
    """
    Provide a minimal dictionary structure mimicking a row from the OSF dataset.
    Used for unit testing logic that expects specific columns.
    
    Note: This is for structural testing only. Do not use for numerical validation.
    """
    return {
        "year": 2015,
        "field": "Psychology",
        "original_study_id": "abc123",
        "effect_size": 0.45,
        "sample_size": 100,
        "p_value": 0.03,
        "power_est": 0.80
    }

@pytest.fixture
def mock_missing_data_dict():
    """
    Provide a dictionary with missing values to test error handling.
    """
    return {
        "year": 2015,
        "field": "Psychology",
        "original_study_id": "abc123",
        "effect_size": None,  # Missing
        "sample_size": 100,
        "p_value": 0.03,
        "power_est": 0.80
    }

@pytest.fixture
def mock_nan_data_dict():
    """
    Provide a dictionary with NaN values to test error handling.
    """
    import math
    return {
        "year": 2015,
        "field": "Psychology",
        "original_study_id": "abc123",
        "effect_size": float('nan'),
        "sample_size": 100,
        "p_value": 0.03,
        "power_est": 0.80
    }

@pytest.fixture
def mock_zero_sample_size_dict():
    """
    Provide a dictionary with zero sample size to test ZeroDivisionError handling.
    """
    return {
        "year": 2015,
        "field": "Psychology",
        "original_study_id": "abc123",
        "effect_size": 0.45,
        "sample_size": 0,
        "p_value": 0.03,
        "power_est": 0.80
    }

@pytest.fixture
def mock_dataframe_from_dict(request):
    """
    Helper fixture to create a pandas DataFrame from a mock dict.
    Usage: def test_something(mock_dataframe_from_dict, mock_sample_data_dict):
    """
    import pandas as pd
    
    def _make_df(data_dict):
        return pd.DataFrame([data_dict])
    
    return _make_df