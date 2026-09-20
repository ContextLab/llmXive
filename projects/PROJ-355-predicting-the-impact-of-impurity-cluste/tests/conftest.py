"""Shared pytest fixtures and configuration for the test suite."""
import os
import sys
from pathlib import Path

# Ensure the project root is in the Python path for imports
# The project root is assumed to be the parent of the 'code' directory
# or the current working directory if run from the repo root.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Optional: Set up a temporary directory for test data if needed
# This can be overridden by specific test fixtures.
import pytest
import tempfile

@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary project-like directory structure for tests."""
    # Create standard subdirectories
    (tmp_path / "code").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "raw").mkdir()
    (tmp_path / "data" / "processed").mkdir()
    (tmp_path / "results").mkdir()
    return tmp_path
