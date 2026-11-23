import pytest
import numpy as np
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_config():
    return {
        "mass": 0.001,
        "radius": 0.005,
        "roughness": 0.05,
        "frequency_bins": [[0.0, 10.0], [10.0, 50.0]]
    }

@pytest.fixture
def synthetic_tracking_data():
    """Generate a small synthetic dataset for unit testing."""
    np.random.seed(42)
    n_rows = 100
    data = {
        "particle_id": np.repeat(1, n_rows),
        "timestamp": np.arange(n_rows) * 0.01,
        "x": np.random.randn(n_rows),
        "y": np.random.randn(n_rows),
        "z": np.random.randn(n_rows),
        "orientation": np.random.randn(n_rows)
    }
    return pd.DataFrame(data)

@pytest.fixture
def synthetic_driving_data():
    """Generate synthetic driving signal data."""
    np.random.seed(42)
    n_rows = 100
    data = {
        "timestamp": np.arange(n_rows) * 0.01,
        "amplitude": np.sin(np.arange(n_rows) * 0.1),
        "frequency": 10.0
    }
    return pd.DataFrame(data)
