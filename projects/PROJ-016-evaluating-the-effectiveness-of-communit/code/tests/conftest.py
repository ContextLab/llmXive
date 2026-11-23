"""
Pytest configuration and fixtures for the llmXive project.
Provides shared fixtures for tests across the project.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure the 'code' directory is in the Python path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project's code directory to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data files during tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log files during tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config(temp_data_dir):
    """Provide a sample configuration dictionary for testing."""
    return {
        "year_range": (2000, 2020),
        "api_endpoints": {
            "fao": "https://api.fao.org",
            "world_bank": "https://api.worldbank.org"
        },
        "data_dirs": {
            "raw": str(temp_data_dir / "raw"),
            "processed": str(temp_data_dir / "processed")
        }
    }

@pytest.fixture
def mock_logger(caplog):
    """Provide a logger fixture that captures logs for testing."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)