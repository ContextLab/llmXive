"""
Pytest configuration and shared fixtures.

This file configures pytest for the project and provides shared fixtures
that can be used across all test modules.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def sample_ar1_data():
    """Fixture providing a sample AR(1) time series."""
    np.random.seed(42)
    n = 100
    rho = 0.5
    epsilon = np.random.normal(0, 1, n)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = rho * x[t-1] + epsilon[t]
    return x


@pytest.fixture(scope="session")
def sample_iid_data():
    """Fixture providing a sample i.i.d. time series."""
    np.random.seed(42)
    return np.random.normal(0, 1, 100)


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path):
    """Fixture providing a temporary directory for output files."""
    return tmp_path / "test_outputs"
