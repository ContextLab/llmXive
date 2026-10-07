"""
Pytest configuration and shared fixtures for the plant root architecture project.
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def project_root_path():
    """Return the root path of the project."""
    # Assume this file is at code/tests/conftest.py, so root is 2 levels up
    return Path(__file__).parent.parent.parent

@pytest.fixture(scope="session")
def code_dir(project_root_path):
    """Return the path to the code directory."""
    return project_root_path / "code"

@pytest.fixture(scope="session")
def data_dir(project_root_path):
    """Return the path to the data directory."""
    return project_root_path / "data"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def figures_dir(project_root_path):
    """Return the path to the figures directory."""
    return project_root_path / "figures"

@pytest.fixture(autouse=True)
def setup_environment(tmp_path):
    """
    Optional fixture to set up temporary environment variables or directories
    for specific test runs if needed.
    """
    yield tmp_path
