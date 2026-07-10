"""
Pytest configuration and fixtures for the plant root architecture project.

This file sets up the test environment, including:
- Adding the project root to sys.path for imports
- Configuring logging for tests
- Defining fixtures for data paths and mock data
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Add the project root to the path so imports work correctly
# Assumes this file is at code/tests/conftest.py
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests to avoid silent failures
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def project_root_path():
    """Return the root path of the project."""
    return project_root

@pytest.fixture
def data_dir(project_root_path):
    """Return the path to the data directory."""
    return project_root_path / "data"

@pytest.fixture
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture
def code_dir(project_root_path):
    """Return the path to the code directory."""
    return project_root_path / "code"
