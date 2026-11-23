"""
Pytest configuration and fixtures for the Statistical Analysis of Feature Importance Drift project.

This file sets up the test environment, ensuring paths are correctly resolved relative
to the project root and configuring logging for test execution.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root (parent of 'tests') to sys.path to allow imports from 'code'
# Assuming the structure is: project_root/tests/conftest.py and project_root/code/...
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging for tests to avoid "No handler found" warnings
# and to ensure logs are visible during test runs.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Optional: Fixture to provide the project root path if needed in tests
@pytest.fixture
def project_root_path():
    return project_root

# Optional: Fixture to provide a temporary data directory for tests
@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

# Optional: Fixture to provide a temporary output directory for tests
@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir

# Optional: Fixture to provide a temporary logs directory for tests
@pytest.fixture
def temp_log_dir(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

# Optional: Fixture to mock configuration if needed (e.g., to avoid file system dependencies)
@pytest.fixture
def mock_config(tmp_path):
    # Create a minimal config structure if the project relies on config files
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # Return path or object as needed
    return config_dir

# Import pytest here to ensure it's available for the fixtures above
import pytest