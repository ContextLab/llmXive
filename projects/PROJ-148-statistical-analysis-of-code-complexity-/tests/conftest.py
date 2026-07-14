"""
Pytest configuration and fixtures for the statistical analysis project.
Ensures the project root is in the Python path for imports.
"""
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_path():
    """Add the project root to sys.path to allow relative imports in tests."""
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
