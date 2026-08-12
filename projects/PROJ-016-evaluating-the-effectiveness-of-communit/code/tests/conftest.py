"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure the code directory is in the Python path for imports
# This allows tests to import modules like `from config import get_config`
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary (though usually not needed for path insertion)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data outputs during tests."""
    tmp_dir = tempfile.mkdtemp(prefix="llmxive_test_data_")
    yield Path(tmp_dir)
    # Cleanup after test
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log outputs during tests."""
    tmp_dir = tempfile.mkdtemp(prefix="llmxive_test_logs_")
    yield Path(tmp_dir)
    # Cleanup after test
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary for testing."""
    return {
        "year_range": (2000, 2020),
        "api_endpoints": {
            "fao": "https://www.fao.org/faostat/en/#data",
            "world_bank": "https://api.worldbank.org/v2"
        },
        "income_groups": ["low", "middle"]
    }

@pytest.fixture
def mock_logger(caplog):
    """Provide a logger that captures logs for testing."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    # Add a handler that writes to caplog
    handler = logging.StreamHandler(caplog.handler.stream)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)