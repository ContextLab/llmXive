"""
Shared pytest fixtures for the llmXive gut microbiome project.

This file provides reusable fixtures for directory paths, sample data,
and temporary directories used across unit, integration, and contract tests.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure the project root is in the path so we can import src modules
# This assumes the tests are run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def setup_path():
    """Returns the path to the setup script."""
    return PROJECT_ROOT / "src" / "setup_data_structure.py"

@pytest.fixture(scope="session")
def project_root():
    """Returns the project root directory."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Returns the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def processed_dir(data_dir):
    """Returns the processed data directory."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def results_dir(processed_dir):
    """Returns the results directory."""
    return processed_dir / "results"

@pytest.fixture(scope="function")
def temp_dir():
    """Creates a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture(scope="function")
def sample_agp_df():
    """
    Creates a sample DataFrame mimicking the structure of AGP data.
    Used for testing ingestion and harmonization logic.
    """
    data = {
        "sample_id": ["AGP_001", "AGP_002", "AGP_003", "AGP_004"],
        "fiber_g_day": [25.0, 15.0, 30.0, 5.0],
        "read_count": [10000, 4000, 12000, 8000],
        "age": [35, 42, 29, 55],
        "bmi": [22.5, 28.0, 24.1, 30.5],
        "antibiotic_use": ["no", "yes", "no", "no"],
        "taxon_A": [0.1, 0.2, 0.15, 0.12],
        "taxon_B": [0.05, 0.08, 0.06, 0.04],
        "cohort_id": ["AGP", "AGP", "AGP", "AGP"]
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="function")
def sample_ukbb_df():
    """
    Creates a sample DataFrame mimicking the structure of UKBB data.
    Used for testing ingestion and harmonization logic.
    """
    data = {
        "sample_id": ["UKBB_101", "UKBB_102", "UKBB_103"],
        "fiber_g_day": [18.0, 22.0, 12.0],
        "read_count": [9000, 11000, 3500],
        "age": [50, 45, 60],
        "bmi": [26.0, 23.5, 29.0],
        "antibiotic_use": ["no", "no", "yes"],
        "taxon_A": [0.11, 0.14, 0.09],
        "taxon_B": [0.07, 0.05, 0.06],
        "cohort_id": ["UKBB", "UKBB", "UKBB"]
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="function")
def sample_clr_df():
    """
    Creates a sample DataFrame with CLR-transformed values.
    Used for testing correlation analysis.
    """
    data = {
        "sample_id": ["S1", "S2", "S3", "S4"],
        "fiber_g_day": [25.0, 15.0, 30.0, 5.0],
        "taxon_A_clr": [-0.5, 0.2, -0.3, 0.1],
        "taxon_B_clr": [0.4, -0.1, 0.3, -0.2],
        "taxon_C_clr": [0.1, 0.1, 0.1, 0.1],
        "age": [35, 42, 29, 55],
        "bmi": [22.5, 28.0, 24.1, 30.5]
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="function")
def sample_covariate_df():
    """
    Creates a sample DataFrame with missing values for covariate testing.
    """
    data = {
        "sample_id": ["C1", "C2", "C3", "C4", "C5"],
        "age": [30.0, np.nan, 45.0, 50.0, np.nan],
        "bmi": [22.0, 25.0, np.nan, 28.0, 30.0],
        "antibiotic_use": ["no", "yes", "no", np.nan, "no"]
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="function")
def temp_input_file(temp_dir):
    """
    Creates a temporary input CSV file for testing file I/O operations.
    Returns the path to the file.
    """
    file_path = temp_dir / "input_test.csv"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture(scope="function")
def temp_output_file(temp_dir):
    """
    Returns a path for a temporary output file.
    The file is not created by the fixture; the test must write to it.
    """
    return temp_dir / "output_test.csv"