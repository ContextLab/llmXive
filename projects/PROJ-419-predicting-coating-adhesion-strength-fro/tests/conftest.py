"""Pytest configuration and shared fixtures for the project."""
import os
import sys
import logging
import pytest

# Ensure the code directory is in the path for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(ROOT_DIR, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return os.path.join(ROOT_DIR, "data", "test")

@pytest.fixture(scope="session")
def code_dir():
    """Provide path to the code directory."""
    return CODE_DIR

@pytest.fixture(scope="function")
def mock_logger(caplog):
    """Provide a logger that captures logs to caplog."""
    return logging.getLogger("test_logger")
