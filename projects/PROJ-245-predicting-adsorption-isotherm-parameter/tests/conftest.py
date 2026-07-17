"""
Pytest configuration and shared fixtures for all test suites.
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Ensure project root is in path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return ROOT_DIR

@pytest.fixture
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    """Return the code directory path."""
    return project_root / "code"

@pytest.fixture
def tests_dir(project_root):
    """Return the tests directory path."""
    return project_root / "tests"

@pytest.fixture
def setup_test_environment(tmp_path, project_root):
    """
    Create a temporary test environment with necessary directory structure.
    Useful for tests that need to write output files.
    """
    # Create temporary data directories
    temp_data = tmp_path / "data"
    temp_data.mkdir(parents=True)
    
    # Copy existing contracts if they exist
    contracts_src = project_root / "contracts"
    if contracts_src.exists():
        import shutil
        shutil.copytree(contracts_src, tmp_path / "contracts")
    
    # Set environment variables for test isolation
    os.environ["DATA_DIR"] = str(temp_data)
    os.environ["PROJECT_ROOT"] = str(project_root)
    
    yield tmp_path
    
    # Cleanup handled by pytest's tmp_path fixture
