"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_trajectory_data():
    """Generate a small, deterministic sample trajectory for testing."""
    np.random.seed(42)
    steps = 10
    dim = 4  # Small dimension for unit tests
    data = []
    for i in range(steps):
        matrix = np.random.randn(dim, dim)
        mean_val = np.mean(matrix)
        var_val = np.var(matrix)
        data.append({
            "step": i,
            "matrix": matrix.tolist(),
            "mean": float(mean_val),
            "var": float(var_val)
        })
    return data


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test artifacts that is cleaned up afterwards."""
    tmp_path = Path(tempfile.mkdtemp())
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)
