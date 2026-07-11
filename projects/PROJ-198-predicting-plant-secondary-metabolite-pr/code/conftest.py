"""
Pytest configuration and fixtures.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd

@pytest.fixture(scope="session")
def ci_mode_env():
    """Fixture to set CI mode environment variable for tests."""
    os.environ["CI_MODE"] = "true"
    yield
    del os.environ["CI_MODE"]

@pytest.fixture(scope="session")
def mock_data_dir(tmp_path_factory):
    """Create a temporary mock data directory structure."""
    base = tmp_path_factory.mktemp("data")
    (base / "raw").mkdir()
    (base / "processed").mkdir()
    (base / "interim").mkdir()
    return base

@pytest.fixture
def sample_aligned_data():
    """Generate a sample aligned dataset for testing."""
    data = {
        "species": ["Arabidopsis thaliana", "Oryza sativa", "Zea mays"],
        "bgc_count": [12, 45, 38],
        "terpene_abundance": [0.15, 0.85, 0.42],
        "alkaloid_abundance": [0.05, 0.12, 0.65],
        "phenolic_abundance": [0.30, 0.10, 0.08]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_model_results():
    """Generate sample model results for testing."""
    return {
        "model_type": "PGLS",
        "r_squared": 0.45,
        "p_value": 0.01,
        "features": ["bgc_count", "terpene_abundance"],
        "coefficients": [0.5, 0.2]
    }
