"""Pytest configuration and shared fixtures."""
import os
import sys
import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    yield
    if root in sys.path:
        sys.path.remove(root)
