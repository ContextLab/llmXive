"""
Pytest configuration and shared fixtures for PROJ-285.

This file configures the test environment, ensuring that:
1. The project root is in the Python path.
2. Logging is configured to avoid cluttering test output.
3. Shared fixtures for data paths are available.
"""
import os
import sys
import logging
import pytest
from pathlib import Path

# Add project root to path to allow imports like `from src.data_loader import ...`
# We assume the test runner is invoked from the project root or code/ directory.
# If running from `code/`, we go up one level.
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging to suppress INFO/DEBUG logs during tests unless explicitly requested
# This prevents test output from being flooded with pipeline logs.
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define paths for fixtures
@pytest.fixture(scope="session")
def project_root_path():
    """Returns the absolute path to the project root."""
    return project_root

@pytest.fixture(scope="session")
def data_raw_path(project_root_path):
    """Returns the path to the data/raw directory."""
    return project_root_path / "data" / "raw"

@pytest.fixture(scope="session")
def data_processed_path(project_root_path):
    """Returns the path to the data/processed directory."""
    return project_root_path / "data" / "processed"

@pytest.fixture(scope="session")
def code_src_path(project_root_path):
    """Returns the path to the code/src directory."""
    return project_root_path / "code" / "src"
