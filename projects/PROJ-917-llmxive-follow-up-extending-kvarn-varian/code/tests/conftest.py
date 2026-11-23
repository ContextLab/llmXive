"""
Pytest configuration and shared fixtures.
"""
import pytest
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_trajectory_data():
    """Generate sample attention trajectory data for testing."""
    steps = 100
    mean = np.random.normal(0.5, 0.1, steps)
    var = np.random.normal(0.01, 0.001, steps)
    skew = np.random.normal(0.0, 0.1, steps)
    kurt = np.random.normal(3.0, 0.2, steps)
    return {
        "mean": mean,
        "var": var,
        "skew": skew,
        "kurt": kurt
    }

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for data output tests."""
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    return generated_dir
