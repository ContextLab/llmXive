"""
Pytest configuration and fixtures for the project.
Ensures the project root and code directories are on the Python path.
"""
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_path():
    """
    Automatically add the project root and code directory to sys.path
    so that imports like `from utils import ...` work in tests.
    """
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__)
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Add to path if not already there
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    yield

    # Cleanup (optional, but good practice)
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def sample_data_dir(tmp_path):
    """
    Fixture providing a temporary directory for test data.
    Returns a Path object to the temp directory.
    """
    return tmp_path

@pytest.fixture
def mock_logger(tmp_path):
    """
    Fixture providing a mock logger that writes to a temp file.
    """
    import logging
    log_file = tmp_path / "test.log"
    
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    yield logger, log_file
    
    logger.removeHandler(handler)
    handler.close()
