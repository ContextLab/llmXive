"""
Pytest configuration and fixtures for the research pipeline.

This file configures the test environment, ensuring that:
1. The project root is added to the Python path.
2. Shared fixtures for configuration and random states are available.
3. Test execution adheres to the project's reproducibility standards.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path to allow imports from 'code' package
# Assumes tests/ is at the same level as code/
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture(scope="function")
def reproducible_seed():
    """
    Fixture providing a reproducible seed for tests.
    Ensures tests relying on randomness are deterministic.
    """
    return 42
