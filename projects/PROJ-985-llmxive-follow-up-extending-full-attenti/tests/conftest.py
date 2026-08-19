"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
import pytest
import logging
from pathlib import Path

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture(scope="session")
def code_dir(project_root):
    """Return the code directory path."""
    return project_root / "code"

@pytest.fixture(scope="session")
def tests_dir(project_root):
    """Return the tests directory path."""
    return project_root / "tests"

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test artifacts."""
    return tmp_path

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    caplog.set_level(logging.INFO)
