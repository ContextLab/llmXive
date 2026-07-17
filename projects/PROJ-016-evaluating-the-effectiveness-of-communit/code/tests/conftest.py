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
import json

# Add parent directory to path to resolve imports like `from config import ...`
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data artifacts during tests."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for log files during tests."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

@pytest.fixture
def sample_config(temp_data_dir):
    """Generate a sample configuration dictionary for testing."""
    config = {
        "year_range": (2000, 2020),
        "api_endpoints": {
            "fao": "https://www.fao.org/api",
            "world_bank": "https://api.worldbank.org/v2"
        },
        "data_paths": {
            "raw": os.path.join(temp_data_dir, "raw"),
            "processed": os.path.join(temp_data_dir, "processed")
        }
    }
    # Ensure directories exist
    Path(config["data_paths"]["raw"]).mkdir(parents=True, exist_ok=True)
    Path(config["data_paths"]["processed"]).mkdir(parents=True, exist_ok=True)
    return config

@pytest.fixture
def mock_logger(temp_logs_dir):
    """Create a temporary logger for testing logging functionality."""
    logger_name = "test_logger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    log_file = os.path.join(temp_logs_dir, "test.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    yield logger
    
    # Cleanup
    logger.handlers.clear()