"""
Pytest configuration and shared fixtures for the temporal discounting project.

This file sets up the test environment, ensuring:
1. The project root is in the Python path for imports.
2. A consistent random seed is used for reproducibility across tests.
3. Temporary directories for test outputs are managed automatically.
"""
import sys
import os
import pytest
from pathlib import Path
from config import get_project_root, get_random_state

# Add project root to path if not already present
PROJECT_ROOT = get_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    """Return the absolute path to the project root directory."""
    return PROJECT_ROOT

@pytest.fixture(scope="function")
def test_output_dir(tmp_path):
    """
    Provide a temporary directory for test outputs.
    
    Tests can write files here, and they will be automatically cleaned up
    after the test function completes.
    """
    return tmp_path

@pytest.fixture(scope="function")
def random_state():
    """
    Provide a reproducible random state generator for tests.
    
    Uses the global seed configuration to ensure test runs are deterministic.
    """
    return get_random_state()

@pytest.fixture(autouse=True)
def set_working_directory():
    """
    Automatically change to the project root before each test.
    
    This ensures that relative paths in code (if any) resolve correctly
    during test execution.
    """
    original_dir = os.getcwd()
    os.chdir(PROJECT_ROOT)
    yield
    os.chdir(original_dir)
