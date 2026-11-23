import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

@pytest.fixture
def setup_path():
    """Provide a temporary path for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def project_root():
    """Return the actual project root."""
    # Assuming code/tests/conftest.py is in the repo
    return Path(__file__).resolve().parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def processed_dir(project_root):
    return project_root / "data" / "processed"

@pytest.fixture
def results_dir(project_root):
    return project_root / "data" / "processed" / "results"

@pytest.fixture
def temp_dir(setup_path):
    return setup_path

@pytest.fixture
def sample_agp_df():
    """Create a sample AGP DataFrame for testing."""
    data = {
        "sample_id": ["AGP_001", "AGP_002", "AGP_003"],
        "read_count": [10000, 4000, 20000],
        "fiber_g_day": [25.0, 10.0, -5.0],
        "age": [30, 45, 50],
        "bmi": [22.0, 25.0, 28.0],
        "antibiotic_use": [0, 1, 0],
        "taxon_a": [0.1, 0.2, 0.3],
        "taxon_b": [0.4, 0.5, 0.6]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_ukbb_df():
    """Create a sample UKBB DataFrame for testing."""
    data = {
        "sample_id": ["UKBB_001", "UKBB_002", "UKBB_003"],
        "read_count": [15000, 3000, 8000],
        "fiber_g_day": [30.0, 15.0, 180.0],
        "age": [25, 60, 35],
        "bmi": [21.0, 30.0, 24.0],
        "antibiotic_use": [0, 0, 1],
        "taxon_a": [0.15, 0.25, 0.35],
        "taxon_b": [0.45, 0.55, 0.65]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_clr_df():
    """Create a sample CLR transformed DataFrame."""
    data = {
        "sample_id": ["S1", "S2"],
        "taxon_a": [0.1, -0.1],
        "taxon_b": [-0.2, 0.2]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_covariate_df():
    """Create a sample covariate DataFrame with missing values."""
    data = {
        "sample_id": ["C1", "C2", "C3", "C4"],
        "age": [20, 30, np.nan, 40],
        "bmi": [22.0, np.nan, 25.0, 28.0],
        "antibiotic_use": [0, 1, 0, np.nan]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_file(setup_path):
    """Create a temporary input file."""
    file_path = setup_path / "input.csv"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def temp_output_file(setup_path):
    """Create a temporary output file path."""
    return setup_path / "output.csv"
