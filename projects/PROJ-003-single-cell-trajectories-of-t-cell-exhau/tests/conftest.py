"""
Shared pytest fixtures and configuration for PROJ-003 tests.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_velocity_data():
    """Generate sample velocity data for testing."""
    np.random.seed(42)
    n_cells = 100
    n_genes = 10
    return {
        "spliced": np.random.rand(n_cells, n_genes),
        "unspliced": np.random.rand(n_cells, n_genes),
        "velocity": np.random.rand(n_cells, n_genes),
        "pseudotime": np.random.rand(n_cells)
    }
