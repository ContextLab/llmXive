"""
Pytest configuration and shared fixtures for llmXive pipeline tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def project_path():
    """Return the project root path."""
    return project_root

@pytest.fixture
def data_path(project_path):
    """Return the data directory path."""
    return project_path / "data"

@pytest.fixture
def output_path(project_path):
    """Return the output directory path."""
    return project_path / "output"

@pytest.fixture
def config_path(project_path):
    """Return the config directory path."""
    return project_path / "code" / "config.py"

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path
