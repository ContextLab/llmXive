import os
import sys
import logging
from pathlib import Path
import pytest

# Add the project root to sys.path to allow imports from 'code' package
# The project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import config to ensure paths are set up correctly
from code.src.utils.config import setup_logging, ensure_directories

def pytest_configure(config):
    """Configure pytest markers and logging."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-scoped fixture to set up the test environment.
    Ensures directories exist and logging is configured.
    """
    # Ensure all necessary directories exist
    ensure_directories()
    
    # Configure logging for tests
    # This uses the same logger setup as the main application
    setup_logging()
    
    # Log test start
    logger = logging.getLogger(__name__)
    logger.info("Test environment setup complete.")
    
    yield
    
    logger.info("Test session finished.")

@pytest.fixture
def sample_data_dir(tmp_path):
    """
    Fixture providing a temporary directory for test data.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_output_dir(tmp_path):
    """
    Fixture providing a temporary directory for test outputs.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
