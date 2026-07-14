"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path to ensure imports work during testing
# Assumes this file is at tests/conftest.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fixtures for test data paths
@pytest.fixture
def project_root_path():
    return project_root

@pytest.fixture
def data_dir(project_root_path):
    return project_root_path / "data"

@pytest.fixture
def synthetic_data_path(data_dir):
    return data_dir / "raw" / "synthetic_adsorption_data.csv"

@pytest.fixture
def contracts_dir(project_root_path):
    return project_root_path / "contracts"

@pytest.fixture
def dataset_schema_path(contracts_dir):
    return contracts_dir / "dataset.schema.yaml"

@pytest.fixture
def model_output_schema_path(contracts_dir):
    return contracts_dir / "model_output.schema.yaml"

# Fixtures for mock data if needed, but prefer real generated data
@pytest.fixture(scope="session")
def setup_test_environment(project_root_path):
    """
    Ensure necessary directories exist for tests.
    """
    dirs = [
        project_root_path / "data" / "raw",
        project_root_path / "data" / "processed",
        project_root_path / "data" / "external",
        project_root_path / "data" / "validation",
        project_root_path / "figures",
        project_root_path / "tests" / "unit",
        project_root_path / "tests" / "integration",
        project_root_path / "tests" / "contract",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    yield
