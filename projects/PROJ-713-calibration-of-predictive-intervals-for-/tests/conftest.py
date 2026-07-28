"""
Pytest configuration and shared fixtures for all tests.

This file provides:
- Global test configuration
- Shared fixtures for common test data
- Test setup/teardown hooks
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure consistent random state for reproducibility
@pytest.fixture(autouse=True)
def set_seed():
    """Set random seed for reproducibility."""
    np.random.seed(42)
    yield
    # No cleanup needed

@pytest.fixture
def sample_time_series_data():
    """Generate sample time series data for testing."""
    np.random.seed(42)
    n = 1000
    dates = pd.date_range(start="2020-01-01", periods=n, freq="H")
    # AR(1) process with seasonality
    values = np.cumsum(np.random.normal(0, 1, n)) + 10 * np.sin(2 * np.pi * np.arange(n) / 24)
    return pd.DataFrame({"timestamp": dates, "value": values})

@pytest.fixture
def sample_forecast_data():
    """Generate sample forecast data for testing."""
    np.random.seed(42)
    n = 1000
    y_true = np.random.normal(100, 10, n)
    y_pred = y_true + np.random.normal(0, 1, n)
    lower_bound = y_pred - 1.5 * 10
    upper_bound = y_pred + 1.5 * 10
    return y_true, y_pred, lower_bound, upper_bound

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary directory for test results."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return results_dir
