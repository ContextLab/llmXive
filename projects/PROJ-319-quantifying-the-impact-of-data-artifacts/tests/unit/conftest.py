"""Pytest configuration and fixtures for unit tests.

This module provides shared fixtures and configuration for the unit test suite.
It ensures the project root is on the Python path and sets up necessary
temporary directories for test execution.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the project root (parent of 'code' and 'tests') is on the path
# so imports like 'from code.io.loader import ...' work correctly.
@pytest.fixture(scope="session", autouse=True)
def setup_path():
    """Add the project root to sys.path for imports."""
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup if necessary (usually not needed for sys.path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts.

    Yields the path to a temporary directory that is cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)
