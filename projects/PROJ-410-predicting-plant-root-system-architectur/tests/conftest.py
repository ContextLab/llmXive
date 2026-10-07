"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def project_root_path():
    return project_root

@pytest.fixture(scope="session")
def code_dir():
    return project_root / "code"

@pytest.fixture(scope="session")
def data_dir():
    return project_root / "data"

@pytest.fixture(scope="session")
def raw_data_dir():
    return data_dir / "raw"

@pytest.fixture(scope="session")
def processed_data_dir():
    return data_dir / "processed"

@pytest.fixture(scope="session")
def figures_dir():
    return data_dir / "figures"

@pytest.fixture(scope="session")
def setup_environment(tmp_path_factory):
    """Setup temporary directories for test artifacts."""
    base = tmp_path_factory.mktemp("test_data")
    processed = base / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return base