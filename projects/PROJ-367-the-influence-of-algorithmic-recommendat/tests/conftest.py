"""
Pytest configuration and shared fixtures for the research pipeline.

This file configures pytest to:
1. Automatically discover tests in this directory and subdirectories.
2. Add the project root to sys.path to allow imports from `code/` modules.
3. Configure logging to output at INFO level during tests.
4. Provide a shared fixture for the project root path.
"""
import sys
import os
import logging
import pytest
from pathlib import Path

# Add the project root to sys.path to allow imports like `from code.metrics import ...`
# We assume this file is at: <project_root>/tests/conftest.py
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging for test runs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture
def project_root_path():
    """Returns the Path object for the project root directory."""
    return project_root

@pytest.fixture
def data_dir(project_root_path):
    """Returns the Path object for the data directory."""
    return project_root_path / "data"

@pytest.fixture
def code_dir(project_root_path):
    """Returns the Path object for the code directory."""
    return project_root_path / "code"
