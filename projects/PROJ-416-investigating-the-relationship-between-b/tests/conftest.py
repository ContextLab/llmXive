"""
Pytest configuration and fixtures
"""
import pytest
import os
from pathlib import Path

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_motion_metrics():
    """Provide sample motion metrics for testing"""
    return {
        'mean_trans_x': 1.5,
        'mean_trans_y': 1.2,
        'mean_trans_z': 1.8,
        'mean_rot_x': 1.0,
        'mean_rot_y': 1.3,
        'mean_rot_z': 1.1,
        'max_trans_x': 2.1,
        'max_trans_y': 1.9,
        'max_trans_z': 2.3,
        'max_rot_x': 1.5,
        'max_rot_y': 1.7,
        'max_rot_z': 1.4
    }

@pytest.fixture
def sample_adjacency_matrix():
    """Provide a sample adjacency matrix for network analysis"""
    import numpy as np
    return np.array([
        [0, 1, 1, 0, 0],
        [1, 0, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [0, 1, 1, 0, 1],
        [0, 0, 1, 1, 0]
    ], dtype=float)

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up test environment variables"""
    # Set test-specific paths
    monkeypatch.setenv('TEST_MODE', 'true')
    yield
    # Cleanup happens automatically with tmp_path
