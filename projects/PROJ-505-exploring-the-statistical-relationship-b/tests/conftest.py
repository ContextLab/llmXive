"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
# Assuming tests/ is at project root, add root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_root_path():
    """Return the root path of the project."""
    return project_root

@pytest.fixture(scope="function")
def temp_output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path