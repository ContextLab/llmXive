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

# Ensure the code directory is in the path so imports work
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for imports."""
    # Get the project root (parent of 'code')
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    code_dir = project_root / "code"
    
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield
    
    # Cleanup if necessary (though path insertion is usually safe to leave)
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data processing tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log file tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary for testing."""
    return {
        "year_range": (2000, 2020),
        "api_endpoints": {
            "fao": "https://www.fao.org",
            "world_bank": "https://api.worldbank.org"
        },
        "data_dirs": {
            "raw": "data/raw",
            "processed": "data/processed"
        }
    }

@pytest.fixture
def mock_logger(temp_logs_dir):
    """Create a mock logger for testing logging functionality."""
    log_file = temp_logs_dir / "test.log"
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Add file handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    yield logger, log_file
    
    logger.removeHandler(handler)
    handler.close()